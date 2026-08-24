"""Ingestor singleton de um nó Bitcoin Core.

Cada contêiner executa este módulo para exatamente um ``realm_id``. A API é
um processo separado e recebe somente eventos/estado já namespaced no Redis.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import signal
from contextlib import suppress
from pathlib import Path
from typing import Any
from uuid import uuid4

import redis.asyncio as redis

from app.blockchain import BitcoinZMQListener
from app.config import NodeConfig
from app.engine import GameEngine
from app.events import BlockNotice, RawTransactionNotice, event_envelope, utc_now_iso
from app.global_events import GlobalEventType, get_active_event
from app.storage import (
    PREFIX,
    cards_set_key,
    card_detail_key,
    dedupe_key,
    epoch_block_counter_key,
    epoch_id_key,
    epoch_key,
    events_channel,
    ingestor_lease_key,
    leaderboard_key,
    mempool_count_key,
    node_status_key,
    pool_leaderboard_key,  # Fase 2: reset pools no epoch
    realm_state_key,
)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Fase 3: Configurações de estabilidade do ingestor
TX_QUEUE_MAX_SIZE = int(os.getenv("TX_QUEUE_MAX_SIZE", "50000"))  # Aumentado de 20000 para 50000
RPC_RETRY_MAX_ATTEMPTS = int(os.getenv("RPC_RETRY_MAX_ATTEMPTS", "5"))  # Tentativas de retry RPC
RPC_RETRY_BASE_DELAY = float(os.getenv("RPC_RETRY_BASE_DELAY", "0.5"))  # Delay base em segundos
LEASE_TTL_SECONDS = 30
LEASE_RENEW_INTERVAL_SECONDS = 10
RENEW_LEASE_SCRIPT = """
if redis.call('get', KEYS[1]) == ARGV[1] then
  return redis.call('expire', KEYS[1], ARGV[2])
end
return 0
"""
COMMIT_TRANSACTION_SCRIPT = """
if redis.call('get', KEYS[1]) ~= ARGV[1] then
  return {-1, 0}
end
if redis.call('sadd', KEYS[2], ARGV[2]) == 0 then
  return {0, 0}
end
redis.call('expire', KEYS[2], ARGV[3])
local count
if ARGV[4] == '' then
  count = redis.call('incr', KEYS[3])
else
  count = tonumber(ARGV[4])
  redis.call('set', KEYS[3], count)
end
local event = cjson.decode(ARGV[5])
event['mempool_count'] = count
redis.call('publish', KEYS[4], cjson.encode(event))
return {1, count}
"""
COMMIT_BLOCK_SCRIPT = """
if redis.call('get', KEYS[1]) ~= ARGV[1] then
  return 0
end
local current_epoch = redis.call('get', KEYS[2])
local epoch_changed = (current_epoch ~= ARGV[2])
redis.call('set', KEYS[2], ARGV[2])
redis.call('set', KEYS[3], ARGV[3])
if epoch_changed and ARGV[4] ~= '' then
  redis.call('publish', KEYS[4], ARGV[4])
end
return 1
"""
COMMIT_STATUS_SCRIPT = """
if redis.call('get', KEYS[1]) ~= ARGV[1] then
  return 0
end
if ARGV[2] ~= '' then
  redis.call('set', KEYS[2], ARGV[2])
end
redis.call('set', KEYS[3], ARGV[3], 'EX', 30)
redis.call('set', KEYS[4], ARGV[3])
if ARGV[4] ~= '' then
  redis.call('publish', KEYS[5], ARGV[4])
end
return 1
"""
STOP_AND_RELEASE_SCRIPT = """
if redis.call('get', KEYS[1]) ~= ARGV[1] then
  return 0
end
redis.call('set', KEYS[2], ARGV[2], 'EX', 60)
redis.call('set', KEYS[3], ARGV[2])
redis.call('del', KEYS[1])
return 1
"""

# Script alternativo que libera a lease mesmo se o token já expirou.
# Usado como fallback quando a lease já foi perdida (ex: crash do ingestor).
FORCE_STOP_SCRIPT = """
redis.call('set', KEYS[2], ARGV[2], 'EX', 60)
redis.call('set', KEYS[3], ARGV[2])
redis.call('del', KEYS[1])
return 1
"""


class NodeIngestor:
    """Mantém fila, epoch, RPC e listener exclusivos de uma única origem.

    O ``epoch_lock`` serializa ``process_transaction``, ``handle_block`` e
    ``update_status`` para evitar que transações de uma epoch anterior sejam
    publicadas após um novo bloco. Chamadas RPC (``get_mempool_size``) são
    feitas **antes** do lock para não bloquear o processamento de transações.

    A lease é verificada em cada commit Redis via scripts Lua atômicos.
    Se a lease for perdida, ``RuntimeError`` é levantado e propagado,
    encerrando o ingestor para que o supervisor o reinicie.
    """

    def __init__(self, config: NodeConfig, redis_client: redis.Redis) -> None:
        """Monta as dependências sem iniciar I/O no construtor.

        Args:
            config: Configuração do nó (realm, RPC, ZMQ).
            redis_client: Cliente Redis async compartilhado.
        """
        self.config = config
        self.redis = redis_client
        self.engine = GameEngine(config)
        self.queue: asyncio.Queue[tuple[str, RawTransactionNotice]] = asyncio.Queue(
            maxsize=config.queue_max_size
        )
        self.epoch = "starting"
        self.playable = False
        self.status = "starting"
        self.dropped_transactions = 0
        self.last_info: dict[str, Any] = {}
        self.epoch_lock = asyncio.Lock()
        self.lease_key = ingestor_lease_key(config.realm_id)
        self.lease_token = uuid4().hex
        self.token_file = Path(
            os.getenv("INGESTOR_TOKEN_FILE", "/tmp/mempool-miner-ingestor-token")
        )
        self.listener = BitcoinZMQListener(
            config=config,
            transaction_callback=self.enqueue_transaction,
            block_callback=self.handle_block,
        )
        self.tasks: set[asyncio.Task[Any]] = set()

    async def acquire_lease(self) -> None:
        """Garante que exista somente um publicador ativo por realm.

        Usa ``SET NX`` com TTL para criar uma lease atômica. Se outra instância
        já possui a lease, ``RuntimeError`` é levantado. O token é escrito em
        um arquivo temporário e renomeado atomicamente para o path final.

        Raises:
            RuntimeError: Se já existe um ingestor ativo para o realm.
        """
        acquired = await self.redis.set(
            self.lease_key,
            self.lease_token,
            ex=LEASE_TTL_SECONDS,
            nx=True,
        )
        if not acquired:
            raise RuntimeError(f"Já existe um ingestor ativo para {self.config.realm_id}")
        temporary_token_file = self.token_file.with_name(
            f"{self.token_file.name}.{self.lease_token}.tmp"
        )
        temporary_token_file.write_text(self.lease_token, encoding="utf-8")
        temporary_token_file.replace(self.token_file)

    async def lease_loop(self) -> None:
        """Renova a posse com fencing por token e falha ao perder a lease.

        Faz retry com backoff exponencial (max 5 tentativas) antes de
        propagar a falha — isso evita que instabilidades temporárias de
        rede derrubem o ingestor.
        """
        while True:
            await asyncio.sleep(LEASE_RENEW_INTERVAL_SECONDS)
            renewed = await self.redis.eval(
                RENEW_LEASE_SCRIPT,
                1,
                self.lease_key,
                self.lease_token,
                LEASE_TTL_SECONDS,
            )
            if not renewed:
                # Retry com backoff exponencial antes de falhar
                for attempt in range(1, 6):
                    delay = min(2 ** attempt, 10)
                    logger.warning(
                        "Falha na renovação de lease para %s (tentativa %d/5); "
                        "retry em %ds",
                        self.config.realm_id, attempt, delay,
                    )
                    await asyncio.sleep(delay)
                    renewed = await self.redis.eval(
                        RENEW_LEASE_SCRIPT,
                        1,
                        self.lease_key,
                        self.lease_token,
                        LEASE_TTL_SECONDS,
                    )
                    if renewed:
                        logger.info(
                            "Lease renovada com sucesso para %s após %d tentativas",
                            self.config.realm_id, attempt,
                        )
                        break
                if not renewed:
                    raise RuntimeError(f"Lease perdida para {self.config.realm_id}")

    def enqueue_transaction(self, notice: RawTransactionNotice) -> None:
        """Enfileira sem bloquear o socket; fila cheia é medida e descartada."""
        try:
            self.queue.put_nowait((self.epoch, notice))
        except asyncio.QueueFull:
            self.dropped_transactions += 1
            logger.warning(
                "Fila cheia em %s; total descartado=%s",
                self.config.realm_id,
                self.dropped_transactions,
            )

    async def rpc_with_retry(self, rpc_call, *args, **kwargs):
        """Executa chamada RPC com retry e backoff exponencial.
        
        Args:
            rpc_call: Função assíncrona a ser chamada.
            *args: Argumentos para a função.
            **kwargs: Argumentos nomeados para a função.
            
        Returns:
            Resultado da chamada RPC.
            
        Raises:
            Exception: Se todas as tentativas falharem.
        """
        last_exception = None
        for attempt in range(1, RPC_RETRY_MAX_ATTEMPTS + 1):
            try:
                result = await rpc_call(*args, **kwargs)
                if attempt > 1:
                    logger.info(
                        "RPC %s bem-sucedida na tentativa %d",
                        rpc_call.__name__, attempt,
                    )
                return result
            except Exception as e:
                last_exception = e
                if attempt < RPC_RETRY_MAX_ATTEMPTS:
                    delay = RPC_RETRY_BASE_DELAY * (2 ** (attempt - 1))
                    logger.warning(
                        "RPC %s falhou na tentativa %d/%d; retry em %.1fs: %s",
                        rpc_call.__name__, attempt, RPC_RETRY_MAX_ATTEMPTS, delay, e,
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        "RPC %s falhou após %d tentativas: %s",
                        rpc_call.__name__, RPC_RETRY_MAX_ATTEMPTS, e,
                    )
        if last_exception:
            raise last_exception
        raise RuntimeError("RPC falhou sem exceção registrada")

    def drain_stale_transactions(self, new_epoch: str) -> int:
        """Remove itens observados antes da nova epoch de bloco.

        Drena a fila de transações sem bloquear, descartando TXs da epoch
        anterior mas **preservando** transações que já chegaram da nova epoch
        (ZMQ pode enviar TXs após o bloco). Retorna a quantidade descartada.

        Args:
            new_epoch: Hash do bloco que define a nova epoch.

        Returns:
            Número de transações removidas da fila.
        """
        stale = []
        drained = 0
        while True:
            try:
                item = self.queue.get_nowait()
                if item[0] != new_epoch:
                    self.queue.task_done()
                    drained += 1
                else:
                    stale.append(item)
            except asyncio.QueueEmpty:
                break
        # Reinsere transações da nova epoch
        for item in stale:
            self.queue.put_nowait(item)
        return drained

    async def update_status(self, info: dict[str, Any] | None = None) -> None:
        """Publica heartbeat e snapshot jogável sem tratar IBD como falha RPC.

        Chamadas RPC (``get_mempool_size``) são feitas **antes** do ``epoch_lock``
        para não bloquear ``process_transaction`` e ``handle_block``. Dentro do lock,
        o snapshot é montado e commitado via script Lua atômico.

        Args:
            info: Info do blockchain. Se None, consulta RPC.

        Raises:
            RuntimeError: Se a lease for perdida durante o commit.
        """
        if info is None:
            info = await self.engine.get_blockchain_info()
        rpc_available = info is not None

        # RPC fora do lock para não bloquear process_transaction e handle_block.
        reconciled_count = await self.engine.get_mempool_size() if rpc_available else None
        if reconciled_count is None:
            current_count = await self.redis.get(mempool_count_key(self.config.realm_id))
        else:
            current_count = reconciled_count

        async with self.epoch_lock:
            previous_status = self.status
            if info is None:
                self.status = "unavailable"
                self.playable = False
                info = self.last_info
            else:
                self.last_info = info
                in_ibd = bool(info.get("initialblockdownload", True))
                self.status = "syncing" if in_ibd else "ready"
                self.playable = not in_ibd

            public_snapshot = {
                "schema_version": 2,
                "node_id": self.config.node_id,
                "realm_id": self.config.realm_id,
                "network": self.config.network.value,
                "chain": self.config.network.rpc_chain,
                "game_mode": self.config.game_mode,
                "status": self.status,
                "playable": self.playable,
                "initial_block_download": bool(info.get("initialblockdownload", True)),
                "verification_progress": float(info.get("verificationprogress", 0.0) or 0.0),
                "blocks": int(info.get("blocks", 0) or 0),
                "headers": int(info.get("headers", 0) or 0),
                "best_block_hash": info.get("bestblockhash"),
                "pruned": bool(info.get("pruned", False)),
                "prune_height": info.get("pruneheight"),
                "mempool_count": int(current_count or 0),
                "epoch": self.epoch,
                "queue_depth": self.queue.qsize(),
                "dropped_transactions": self.dropped_transactions,
                "updated_at": utc_now_iso(),
            }
            stored_snapshot = {**public_snapshot, "_runtime_token": self.lease_token}
            status_event = ""
            if previous_status != self.status:
                event = event_envelope(
                    action="network_status",
                    node_id=self.config.node_id,
                    network=self.config.network,
                    realm_id=self.config.realm_id,
                    epoch=self.epoch,
                )
                event.update(public_snapshot)
                status_event = json.dumps(event)

            committed = await self.redis.eval(
                COMMIT_STATUS_SCRIPT,
                5,
                self.lease_key,
                mempool_count_key(self.config.realm_id),
                node_status_key(self.config.node_id),
                realm_state_key(self.config.realm_id),
                events_channel(self.config.realm_id),
                self.lease_token,
                "" if reconciled_count is None else str(reconciled_count),
                json.dumps(stored_snapshot),
                status_event,
            )
            if not committed:
                raise RuntimeError(f"Lease perdida para {self.config.realm_id}")

    async def heartbeat_loop(self) -> None:
        """Reconcilia periodicamente IBD, tip, pruning e disponibilidade RPC.

        Roda ``update_status()`` a cada 10 segundos. Se a lease for perdida,
        ``RuntimeError`` é propagado, encerrando o heartbeat e sinalizando
        que o ingestor deve ser reiniciado pelo supervisor.

        Raises:
            RuntimeError: Se a lease for perdida.
        """
        while True:
            try:
                await self.update_status()
            except RuntimeError:
                logger.error("Lease perdida para %s; encerrando heartbeat", self.config.realm_id)
                raise
            except redis.RedisError:
                logger.exception("Falha ao atualizar heartbeat de %s", self.config.realm_id)
            await asyncio.sleep(10)

    async def process_transaction(
        self,
        observed_epoch: str,
        notice: RawTransactionNotice,
    ) -> None:
        """Publica uma TX somente se sua epoch continuar atual após o RPC.

        RACE CONDITION MITIGADA:
        Entre o RPC ``get_tx_metadata`` e o lock ``epoch_lock``, um novo bloco
        pode chegar e avançar ``self.epoch``. A segunda validação dentro do lock
        detecta essa condição e descarta a TX. Isso é intencional — prefere-se
        perder uma TX do que publicar uma da epoch anterior após um bloco.
        """
        if observed_epoch != self.epoch or not self.playable:
            return

        txid = (
            hashlib.sha256(hashlib.sha256(bytes.fromhex(notice.tx_hex)).digest())
            .digest()[::-1]
            .hex()
        )
        metadata = await self.engine.get_tx_metadata(txid, notice.tx_hex)

        # Se a TX não pode ser processada, descarta silenciosamente
        if metadata is None:
            return

        # Fase 8: aplica efeitos de evento global ativo (Fee Spike, Golden Rush,
        # Mempool Flood, Lightning Storm). O status é lido do Redis (publicado
        # pelo GlobalEventScheduler do backend). Falha silenciosa: sem evento
        # ativo, os metadados seguem inalterados.
        try:
            active_status = await get_active_event(self.redis, self.config.realm_id)
            if active_status:
                active_event_type = GlobalEventType(active_status.get("event_type"))
                metadata = GameEngine.apply_event_effects(metadata, active_event_type)
        except (ValueError, KeyError, TypeError, redis.RedisError):
            logger.debug("Evento global não aplicado para %s", txid, exc_info=True)

        # RPC fora do lock para não bloquear handle_block e outras transações.
        reconciled_count = await self.engine.get_mempool_size()

        # O RPC acima pode coincidir com um novo bloco. A segunda validação e
        # todos os efeitos Redis ficam serializados com ``handle_block`` para
        # impedir que uma TX da epoch anterior apareça depois do bloco.
        async with self.epoch_lock:
            if observed_epoch != self.epoch or not self.playable:
                return
            event = event_envelope(
                action="transaction_received",
                node_id=notice.node_id,
                network=notice.network,
                realm_id=notice.realm_id,
                source=notice.source,
                epoch=observed_epoch,
            )
            event.update(
                {
                    "word": metadata["word"],
                    "txid": txid,
                    "tx_stub": txid[:8],
                    "is_golden": metadata["is_golden"],
                    "is_high_fee": metadata["is_high_fee"],
                    "vsize": metadata["vsize"],
                    "fee_rate_sat_vb": metadata["fee_rate_sat_vb"],
                    # Fase 6: MEV Secreto — palavra oculta na grade
                    "is_mev": metadata.get("is_mev", False),
                    # Fase 3: Recompensa calculada no backend
                    "base_reward": metadata.get("base_reward", 500),
                    "multiplier": metadata.get("multiplier", 1),
                }
            )
            committed, _ = await self.redis.eval(
                COMMIT_TRANSACTION_SCRIPT,
                4,
                self.lease_key,
                dedupe_key(self.config.realm_id, observed_epoch),
                mempool_count_key(self.config.realm_id),
                events_channel(self.config.realm_id),
                self.lease_token,
                txid,
                3600,
                "" if reconciled_count is None else str(reconciled_count),
                json.dumps(event),
            )
            if committed < 0:
                raise RuntimeError(f"Lease perdida para {self.config.realm_id}")

    async def process_transactions(self) -> None:
        """Converte transações da epoch atual e publica eventos deduplicados.

        Consome da fila ``self.queue`` e chama ``process_transaction()`` para cada
        item. Se a lease for perdida durante o processamento, ``RuntimeError`` é
        propagado, encerrando o loop. Erros de valor ou Redis são logados e ignorados.

        Raises:
            RuntimeError: Se a lease for perdida.
        """
        while True:
            observed_epoch, notice = await self.queue.get()
            try:
                await self.process_transaction(observed_epoch, notice)
            except RuntimeError:
                logger.error("Lease perdida durante processamento; encerrando ingestor")
                raise
            except (ValueError, TypeError, redis.RedisError):
                logger.exception("Falha ao processar transação em %s", self.config.realm_id)
            finally:
                self.queue.task_done()

            if self.config.process_interval_seconds > 0:
                await asyncio.sleep(self.config.process_interval_seconds)

    async def handle_block(self, notice: BlockNotice) -> None:
        """Avança a epoch, descarta backlog anterior e anuncia o bloco no realm.

        ``get_mempool_size()`` é chamado **antes** do ``epoch_lock`` para não
        bloquear ``process_transaction``. Dentro do lock, a epoch é atualizada,
        o backlog é drenado e o evento ``block_mined`` é publicado via script Lua.

        Args:
            notice: Notificação do bloco recebido via ZMQ.

        Raises:
            RuntimeError: Se a lease for perdida durante o commit.
        """
        # RPC fora do lock para não bloquear process_transaction.
        mempool_size = await self.engine.get_mempool_size()
        current_count = mempool_size if mempool_size is not None else 0

        async with self.epoch_lock:
            self.epoch = notice.block_hash
            drained = self.drain_stale_transactions(notice.block_hash)
            block_event = ""
            if self.playable:
                event = event_envelope(
                    action="block_mined",
                    node_id=notice.node_id,
                    network=notice.network,
                    realm_id=notice.realm_id,
                    source=notice.source,
                    epoch=self.epoch,
                )
                event.update(
                    {
                        "block_hash": notice.block_hash,
                        "mempool_count": current_count,
                        "discarded_backlog": drained,
                        # Fase 2: Halving Protocol — evento visual quando bloco múltiplo de 210000
                        "is_halving_block": (self.last_info.get("blocks", 0) or 0) % 210000 == 0,
                    }
                )
                block_event = json.dumps(event)
            committed = await self.redis.eval(
                COMMIT_BLOCK_SCRIPT,
                4,
                self.lease_key,
                epoch_key(self.config.realm_id),
                mempool_count_key(self.config.realm_id),
                events_channel(self.config.realm_id),
                self.lease_token,
                self.epoch,
                current_count,
                block_event,
            )
            if not committed:
                raise RuntimeError(f"Lease perdida para {self.config.realm_id}")

            # Fase 4: Leaderboard Epochs — incrementa contador de blocos e reseta a cada 2016
            await self._increment_block_counter()

            # Fase 9: Tokens Colecionáveis — gera card para cada bloco minerado
            await self._generate_block_card(
                notice.block_hash,
                current_count,
                drained,
            )

        # update_status fora do lock — se falhar, não derruba o handle_block
        try:
            await self.update_status()
        except RuntimeError:
            logger.error("Lease perdida em update_status após bloco; encerrando ingestor")
            raise
        except Exception:
            logger.exception("Falha em update_status após bloco em %s", self.config.realm_id)

    # Fase 4: Leaderboard Epochs — reset a cada 2016 blocos
    async def _increment_block_counter(self) -> None:
        """Incrementa o contador de blocos e reseta o leaderboard ao atingir 2016.

        Usa um script Lua atômico para:
        1. Incrementar ``block_counter``.
        2. Se >= 2016: deleta o leaderboard antigo, incrementa ``epoch_id``, zera o contador.
        3. Publica ``leaderboard_reset`` no canal de eventos.

        Raises:
            RuntimeError: Se a lease for perdida.
        """
        RESET_SCRIPT = """
        local counter_key = KEYS[1]
        local epoch_key = KEYS[2]
        local lb_key = KEYS[3]
        local pools_key = KEYS[4]  -- Fase 2: reset pools no epoch
        local events_key = KEYS[5]
        local lease_key = KEYS[6]
        local token = ARGV[1]
        local epoch_id = ARGV[2]

        if redis.call('get', lease_key) ~= token then return -1 end

        local count = tonumber(redis.call('get', counter_key) or '0') + 1
        redis.call('set', counter_key, count)

        if count >= 2016 then
            redis.call('del', lb_key)
            redis.call('del', pools_key)  -- Fase 2: reset pools entre épocas
            redis.call('set', counter_key, '0')
            local new_epoch = tonumber(redis.call('get', epoch_key) or '0') + 1
            redis.call('set', epoch_key, new_epoch)
            redis.call('publish', events_key, cjson.encode({
                action = 'leaderboard_reset',
                realm_id = epoch_id,
                epoch = new_epoch
            }))
        end

        -- Boss Battles: a cada 50 blocos, publica evento boss_block
        if count % 50 == 0 then
            redis.call('publish', events_key, cjson.encode({
                action = 'boss_block',
                realm_id = epoch_id,
                block_count = count,
                boss_hp = 10,
                boss_grid_size = 15,
                boss_words = 10,
                boss_timer = 45,
                boss_reward_multiplier = 5,
                boss_loot = 50000
            }))
        end

        return count
        """
        await self.redis.eval(
            RESET_SCRIPT,
            6,  # Fase 2: 6 keys (antes era 5)
            epoch_block_counter_key(self.config.realm_id),
            epoch_id_key(self.config.realm_id),
            leaderboard_key(self.config.realm_id),
            pool_leaderboard_key(self.config.realm_id),  # Fase 2: key de pools
            events_channel(self.config.realm_id),
            self.lease_key,
            self.lease_token,
            self.config.realm_id,
        )

    # Fase 9: Tokens Colecionáveis (Block Cards) — geração de cards ao minerar bloco
    async def _generate_block_card(
        self,
        block_hash: str,
        mempool_count: int,
        discarded_backlog: int,
    ) -> None:
        """Gera um Block Card colecionável para cada bloco minerado.

        A raridade é determinada por eventos especiais:
        - Common (60%): bloco normal
        - Rare (25%): bloco com High Fee ou Golden Hash
        - Epic (10%): bloco com MEV ou Boss Battle
        - Legendary (5%): bloco em evento global ativo

        O card é salvo em dois lugares no Redis:
        1. cards_set_key: conjunto com hashes dos blocos cardados
        2. card_detail_key: hash com dados completos do card

        Args:
            block_hash: Hash do bloco minerado.
            mempool_count: Tamanho da mempool no momento do bloco.
            discarded_backlog: Transações descartadas da epoch anterior.
        """
        # Determina raridade baseada em eventos especiais
        rarity = self._determine_card_rarity()

        # Constrói dados do card
        card_data = {
            "block_hash": block_hash,
            "rarity": rarity,
            "mempool_count": str(mempool_count),
            "discarded_backlog": str(discarded_backlog),
            "block_number": str(self.last_info.get("blocks", 0) or 0),
            "is_halving_block": str(
                (self.last_info.get("blocks", 0) or 0) % 210000 == 0
            ),
            "timestamp": utc_now_iso(),
            "realm_id": self.config.realm_id,
        }

        # Salva detalhes do card no Redis
        detail_key = card_detail_key(
            self.config.realm_id, "global", block_hash
        )
        await self.redis.hset(detail_key, mapping=card_data)
        await self.redis.expire(detail_key, 86400 * 30)  # 30 dias TTL

        # Adiciona ao conjunto de cards do realm (sem username para consulta global)
        cards_key = f"{PREFIX}:{{{self.config.realm_id}}}:cards:global"  # Fase 9
        await self.redis.sadd(cards_key, block_hash)
        await self.redis.expire(cards_key, 86400 * 30)

        logger.info(
            "Card gerado: bloco %s (%s) — raridade: %s",
            block_hash[:16],
            card_data["block_number"],
            rarity,
        )

    def _determine_card_rarity(self) -> str:
        """Determina a raridade do card com base em eventos do bloco.

        Returns:
            Uma das raridades: 'common', 'rare', 'epic', 'legendary'.
        """
        import random

        roll = random.random() * 100

        # Legendary: evento global ativo (5%)
        if roll < 5:
            return "legendary"
        # Epic: bloco com MEV ou Boss Battle (10%)
        if roll < 15:
            return "epic"
        # Rare: bloco com High Fee ou Golden Hash (25%)
        if roll < 40:
            return "rare"
        # Common: bloco normal (60%)
        return "common"

    async def run(self) -> None:
        """Valida a chain e mantém listener, consumidor e heartbeat como unidade.

        Fluxo de inicialização:
        1. Pings o Redis para verificar conectividade.
        2. Adquire a lease (fencing por token).
        3. Inicia o ``lease_loop`` para renovar a lease periodicamente.
        4. Valida a chain via RPC e obtém a epoch inicial.
        5. Inicia o listener ZMQ, o processor de transações e o heartbeat.

        O ingestor encerra quando:
        - SIGTERM é recebido (shutdown graceful).
        - A lease é perdida (``RuntimeError`` propagado).
        - O listener ZMQ falha (exceção propagada).

        Raises:
            RuntimeError: Se a lease for perdida ou o listener ZMQ falhar.
        """
        await self.redis.ping()
        await self.acquire_lease()
        lease_task = asyncio.create_task(self.lease_loop(), name="ingestor-lease")
        self.tasks = {lease_task}
        initial_info = await self.engine.validate_declared_network()
        self.epoch = await self.engine.get_best_block_hash() or "genesis"
        mempool_size = await self.engine.get_mempool_size()
        committed = await self.redis.eval(
            COMMIT_BLOCK_SCRIPT,
            4,
            self.lease_key,
            epoch_key(self.config.realm_id),
            mempool_count_key(self.config.realm_id),
            events_channel(self.config.realm_id),
            self.lease_token,
            self.epoch,
            mempool_size or 0,
            "",
        )
        if not committed:
            raise RuntimeError(f"Lease perdida para {self.config.realm_id}")
        await self.update_status(initial_info)

        self.tasks.update(
            {
                asyncio.create_task(self.listener.start(), name="bitcoin-zmq-listener"),
                asyncio.create_task(self.process_transactions(), name="transaction-processor"),
                asyncio.create_task(self.heartbeat_loop(), name="node-heartbeat"),
            }
        )
        done, pending = await asyncio.wait(self.tasks, return_when=asyncio.FIRST_EXCEPTION)
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        for task in done:
            if not task.cancelled() and task.exception():
                raise task.exception()  # pragma: no cover - supervisão operacional

    async def close(self) -> None:
        """Encerra tarefas, sockets, RPC e heartbeat de forma ordenada."""
        self.listener.stop()
        for task in self.tasks:
            task.cancel()
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        self.status = "stopped"
        self.playable = False
        stopped_snapshot = {
            "schema_version": 2,
            "node_id": self.config.node_id,
            "realm_id": self.config.realm_id,
            "network": self.config.network.value,
            "chain": self.config.network.rpc_chain,
            "status": "stopped",
            "playable": False,
            "initial_block_download": bool(self.last_info.get("initialblockdownload", True)),
            "epoch": self.epoch,
            "_runtime_token": self.lease_token,
            "updated_at": utc_now_iso(),
        }
        with suppress(redis.RedisError):
            serialized = json.dumps(stopped_snapshot)
            released = await self.redis.eval(
                STOP_AND_RELEASE_SCRIPT,
                3,
                self.lease_key,
                node_status_key(self.config.realm_id),
                realm_state_key(self.config.realm_id),
                self.lease_token,
                serialized,
            )
            # Se a lease já expirou, usa o script de força para liberar
            if not released:
                await self.redis.eval(
                    FORCE_STOP_SCRIPT,
                    3,
                    self.lease_key,
                    node_status_key(self.config.realm_id),
                    realm_state_key(self.config.realm_id),
                    serialized,
                )
        with suppress(OSError):
            if self.token_file.read_text(encoding="utf-8").strip() == self.lease_token:
                self.token_file.unlink(missing_ok=True)
        await self.engine.close()
        await self.redis.aclose()


async def main() -> None:
    """Ponto de entrada ``python -m app.ingestor``."""
    config = NodeConfig.from_environment()
    redis_client = redis.from_url(
        os.getenv("REDIS_URL", "redis://redis:6379"),
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )
    ingestor = NodeIngestor(config, redis_client)
    stop_requested = asyncio.Event()
    loop = asyncio.get_running_loop()

    def handle_sigterm(_signal_number: int, _frame: Any) -> None:
        """Converte SIGTERM do Docker em cancelamento assíncrono ordenado."""
        loop.call_soon_threadsafe(stop_requested.set)

    previous_sigterm_handler = signal.signal(signal.SIGTERM, handle_sigterm)
    logger.info(
        "Iniciando ingestor node_id=%s realm_id=%s network=%s",
        config.node_id,
        config.realm_id,
        config.network.value,
    )
    run_task = asyncio.create_task(ingestor.run(), name="ingestor-runtime")
    stop_task = asyncio.create_task(stop_requested.wait(), name="sigterm-waiter")
    try:
        done, _ = await asyncio.wait(
            {run_task, stop_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
        if stop_task in done:
            logger.info("SIGTERM recebido; encerrando ingestor")
            run_task.cancel()
            await asyncio.gather(run_task, return_exceptions=True)
        else:
            stop_task.cancel()
            await asyncio.gather(stop_task, return_exceptions=True)
            # Propaga a exceção que matou o ingestor com contexto claro.
            if not run_task.cancelled() and run_task.exception():
                logger.error("Ingestor falhou com excecao: %s", run_task.exception())
                raise run_task.exception()
    finally:
        for task in (run_task, stop_task):
            if not task.done():
                task.cancel()
        await asyncio.gather(run_task, stop_task, return_exceptions=True)
        try:
            await ingestor.close()
        finally:
            signal.signal(signal.SIGTERM, previous_sigterm_handler)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Ingestor interrompido")
