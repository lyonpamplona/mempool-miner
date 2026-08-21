"""Motor de metadados de transações e integração RPC com o Bitcoin Core."""

from __future__ import annotations

import asyncio
import base64
import logging
import os
from pathlib import Path
from typing import Any

import httpx
from mnemonic import Mnemonic

from app.config import NodeConfig
from app.global_events import GlobalEventType

logger = logging.getLogger(__name__)


class GameEngine:
    """Converte transações em palavras BIP39 e consulta metadados no Bitcoin Core.

    A configuração é carregada de ``NodeConfig`` e acessada via ``self.config``
    para evitar duplicação de atributos. O cliente HTTP pode ser injetado em testes.

    O cálculo de taxa de fee usa fallback para ``fee`` direto quando ``fees.base``
    está ausente (Bitcoin Core v0.21+ deprecou o campo aninhado).
    """

    def __init__(
        self,
        config: NodeConfig | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Inicializa o motor com configuração e cliente HTTP injetável.

        Args:
            config: Configuração do nó. Se None, carrega do ambiente.
            http_client: Cliente HTTP para RPC. Se None, cria um com timeout de 10s
                (maior para tolerar IBD do signet/mainnet).
        """
        self.config = config or NodeConfig.from_environment()
        self.mnemo = Mnemonic("english")

        # Tenta ler o cookie de autenticação do Bitcoin Core
        self.auth_header = self._load_auth_header()
        self._owns_http_client = http_client is None
        self.http_client = http_client or httpx.AsyncClient(
            timeout=10.0,
            limits=httpx.Limits(max_connections=10),
        )

    def _load_auth_header(self) -> dict[str, str]:
        """Tenta ler o cookie de autenticação do Bitcoin Core.

        Se o arquivo .cookie existir, usa autenticação baseada em cookie.
        Caso contrário, usa autenticação básica com as credenciais do ambiente.
        """
        # Tenta ler o cookie de autenticação
        cookie_paths = [
            f"/home/bitcoin/.bitcoin/{self.config.network.value}/.cookie",
            f"/home/bitcoin/.bitcoin/.cookie",
        ]
        for cookie_path in cookie_paths:
            try:
                cookie_file = Path(cookie_path)
                if cookie_file.exists():
                    cookie_content = cookie_file.read_text().strip()
                    if ":" in cookie_content:
                        user, password = cookie_content.split(":", 1)
                        auth = f"{user}:{password}".encode()
                        token = base64.b64encode(auth).decode()
                        return {"Authorization": f"Basic {token}"}
            except (OSError, ValueError) as exc:
                logger.debug("Falha ao ler cookie de autenticação %s: %s", cookie_path, exc)

        # Fallback para autenticação básica
        auth = f"{self.config.rpc_user}:{self.config.rpc_password}".encode()
        token = base64.b64encode(auth).decode()
        return {"Authorization": f"Basic {token}"}

    def tx_to_word(self, txid: str) -> str:
        """Deriva uma palavra BIP39 determinística dos primeiros 128 bits do TXID.

        Em caso de TXID inválido, devolve BITCOIN para manter o fluxo do jogo
        operacional sem propagar dados sensíveis ou detalhes internos ao cliente.
        """
        try:
            if len(txid) < 32:
                raise ValueError("TXID curto demais para gerar entropia BIP39")
            entropy = bytes.fromhex(txid[:32])
            return self.mnemo.to_mnemonic(entropy).split()[0].upper()
        except (ValueError, IndexError):
            logger.warning("TXID inválido recebido para conversão em palavra")
            return "BITCOIN"

    async def _rpc_call(self, method: str, params: list[Any]) -> Any:
        """Executa uma chamada JSON-RPC e retorna apenas o campo result.

        None é retornado quando o nó está indisponível, responde com erro ou
        devolve um documento inválido. A falha fica registrada no log do serviço.

        Args:
            method: Método JSON-RPC (ex: ``getmempoolentry``, ``getblockchaininfo``).
            params: Lista de parâmetros do método.

        Returns:
            Campo ``result`` da resposta, ou ``None`` em caso de falha.
        """
        payload = {
            "jsonrpc": "1.0",
            "id": f"mempool_miner_{self.config.node_id}",
            "method": method,
            "params": params,
        }

        try:
            response = await self.http_client.post(
                self.config.rpc_url,
                headers=self.auth_header,
                json=payload,
            )
            response.raise_for_status()
            document = response.json()
            if not isinstance(document, dict):
                logger.warning("Bitcoin RPC %s devolveu documento não-objeto", method)
                return None
            if document.get("error"):
                logger.warning("Bitcoin RPC %s retornou erro: %s", method, document["error"])
                return None
            return document.get("result")
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            logger.warning("Falha na chamada Bitcoin RPC %s: %s", method, exc)
            return None

    async def get_tx_metadata(self, txid: str, tx_hex: str | None = None) -> dict[str, Any] | None:
        """Obtém palavra, raridade, taxa efetiva e tamanho virtual da transação.

        Usa ``getmempoolentry`` do Bitcoin Core. Quando ``fees.base`` está ausente
        (Bitcoin Core v0.21+), faz fallback para o campo ``fee`` direto.

        Se ``tx_hex`` for fornecido, calcula o vsize diretamente do hex da TX,
        sem depender de RPC. Isso é necessário em redes como signet onde:
        - TXs são mineradas rapidamente (antes do ingestor processar)
        - ``txindex`` não está habilitado (getrawtransaction não funciona)

        Faz retry com backoff curto (3 tentativas, 500ms) para tolerar
        falhas temporárias de RPC durante IBD.

        Args:
            txid: ID da transação.
            tx_hex: Hex da transação raw (opcional, do ZMQ).

        Returns:
            Dict com ``word``, ``is_golden``, ``is_high_fee``, ``vsize``, ``fee_rate_sat_vb``,
            ou ``None`` se a transação não puder ser encontrada.
        """
        is_golden = txid.startswith("00")
        is_high_fee = False
        vsize = 250
        fee_rate_sat_vb = 0.0

        result = None
        for attempt in range(3):
            result = await self._rpc_call("getmempoolentry", [txid])
            if result is not None:
                break
            if attempt < 2:
                await asyncio.sleep(0.5)

        if isinstance(result, dict):
            candidate_vsize = result.get("vsize", vsize)
            if isinstance(candidate_vsize, (int, float)) and candidate_vsize > 0:
                vsize = int(candidate_vsize)

            fees = result.get("fees", {})
            base_fee_btc = fees.get("base", 0) if isinstance(fees, dict) else 0
            # Bitcoin Core v0.21+ deprecou `fees.base`; usa `fee` direto.
            # Fallback para `fee` quando `fees` está ausente ou vazio.
            if not isinstance(base_fee_btc, (int, float)) or base_fee_btc == 0:
                direct_fee = result.get("fee")
                if isinstance(direct_fee, (int, float)) and direct_fee > 0:
                    base_fee_btc = direct_fee
            if isinstance(base_fee_btc, (int, float)):
                fee_rate_sat_vb = (float(base_fee_btc) * 100_000_000) / vsize
                is_high_fee = fee_rate_sat_vb >= self.config.high_fee_rate_sat_vb
        else:
            # Fallback: calcula vsize diretamente do hex da TX
            if tx_hex:
                vsize = self._calculate_vsize_from_hex(tx_hex)
                logger.debug("TX %s calculada do hex: vsize=%d", txid[:8], vsize)
            else:
                logger.debug("TX %s não encontrada (sem mempoolentry e sem hex)", txid[:8])
                return None

        # MEV: critério unificado — ~15% de chance baseado nos primeiros 8 hex chars do txid
        is_mev = int(txid[:8], 16) % 100 < 15

        return {
            "word": self.tx_to_word(txid),
            "is_golden": is_golden,
            "is_high_fee": is_high_fee,
            "vsize": vsize,
            "fee_rate_sat_vb": round(fee_rate_sat_vb, 2),
            "is_mev": is_mev,
            "expand_grid": vsize > 1000,
            "base_reward": 500,
            "multiplier": self._calculate_multiplier(is_golden, is_high_fee, is_mev),
        }

    @staticmethod
    def _calculate_vsize_from_hex(tx_hex: str) -> int:
        """Calcula o vsize (virtual size) de uma transação a partir do hex raw.

        Implementa parsing básico de transações Bitcoin para calcular o weight
        e derivar o vsize = weight / 4.

        Suporta transações com e sem SegWit (version 2 com witness).

        Args:
            tx_hex: Hex da transação raw (sem prefixo 0x).

        Returns:
            vsize em vBytes (weight / 4).
        """
        try:
            tx_bytes = bytes.fromhex(tx_hex)
        except ValueError:
            return 250  # Fallback

        import struct

        pos = 0

        def read_byte() -> int:
            nonlocal pos
            val = tx_bytes[pos]
            pos += 1
            return val

        def read_uint32() -> int:
            nonlocal pos
            val = struct.unpack_from("<I", tx_bytes, pos)[0]
            pos += 4
            return val

        def read_varint() -> int:
            nonlocal pos
            val = tx_bytes[pos]
            pos += 1
            if val < 0xFD:
                return val
            elif val == 0xFD:
                return struct.unpack_from("<H", tx_bytes, pos)[0]
            elif val == 0xFE:
                return struct.unpack_from("<I", tx_bytes, pos)[0]
            else:
                return struct.unpack_from("<Q", tx_bytes, pos)[0]

        def skip_varint() -> None:
            nonlocal pos
            val = tx_bytes[pos]
            pos += 1
            if val >= 0xFD:
                pos += (val - 0xFD + 1) * 2

        # version (4 bytes)
        pos += 4

        # Inputs
        n_inputs = read_varint()
        has_witness = n_inputs > 0
        for _ in range(n_inputs):
            # prevout (32 + 4)
            pos += 36
            # scriptSig length + data
            skip_varint()
            # sequence (4)
            pos += 4

        # Outputs
        n_outputs = read_varint()
        for _ in range(n_outputs):
            # value (8)
            pos += 8
            # scriptPubKey length + data
            skip_varint()

        # Check for SegWit marker
        if pos < len(tx_bytes):
            marker = read_byte()
            if marker == 0:
                # SegWit transaction
                flag = read_byte()
                if flag != 0:
                    has_witness = True
                else:
                    has_witness = False

        # Calculate base size (without witness)
        base_size = pos

        # Parse witness data if present
        if has_witness:
            for _ in range(n_inputs):
                n_items = read_varint()
                for _ in range(n_items):
                    skip_varint()

        # lockTime (4 bytes)
        pos += 4

        # Calculate weight: base_size * 3 + total_size
        total_size = pos
        weight = base_size * 3 + total_size
        vsize = max(1, weight // 4)

        return vsize

    @staticmethod
    def _calculate_multiplier(is_golden: bool, is_high_fee: bool, is_mev: bool) -> float:
        """Calcula o multiplicador de recompensa com base na raridade da transação.

        Regras:
        - GOLDEN HASH (txid começa com "00"): 5×
        - HIGH FEE (taxa >= 20 sat/vB): 3×
        - MEV (hash especial): 1× (sem multiplicador, mas flag separada)
        - STD: 1×
        - GOLDEN + HIGH FEE: 15× (5× × 3×)
        - GOLDEN + MEV: 5×
        - HIGH FEE + MEV: 3×
        - GOLDEN + HIGH FEE + MEV: 15×
        """
        multiplier = 1.0
        if is_golden:
            multiplier *= 5.0
        if is_high_fee:
            multiplier *= 3.0
        return multiplier

    # ==========================================================================
    # Fase 8: Efeitos de Eventos Globais
    # ==========================================================================

    @staticmethod
    def apply_event_effects(
        tx_metadata: dict[str, Any],
        active_event_type: GlobalEventType | None = None,
    ) -> dict[str, Any]:
        """Aplica efeitos de evento global aos metadados de uma transação.

        Modifica os campos da transação com base no evento ativo:
        - Fee Spike:     Todas as palavras são High Fee (3× recompensa)
        - Golden Rush:   Golden Hash 3× mais frequente (5× recompensa)
        - Mempool Flood: Recompensas 2× (grade 15×15 obrigatória)
        - Lightning Storm: 10× recompensa (8×8 grid)

        Args:
            tx_metadata: Metadados da transação (modificados in-place).
            active_event_type: Tipo de evento global ativo, ou None.

        Returns:
            Metadados modificados com efeitos aplicados.
        """
        if active_event_type is None:
            return tx_metadata

        event_type = active_event_type
        is_golden = tx_metadata.get("is_golden", False)
        is_high_fee = tx_metadata.get("is_high_fee", False)
        multiplier = tx_metadata.get("multiplier", 1.0)

        if event_type == GlobalEventType.FEE_SPIKE:
            # Fee Spike: todas as palavras são High Fee por 10 min (3× recompensa)
            tx_metadata["is_high_fee"] = True
            # Recalcula multiplicador com high_fee
            if not is_golden:
                multiplier = 3.0
            # Golden + High Fee = 15×
            elif is_golden:
                multiplier = 15.0
            tx_metadata["multiplier"] = multiplier

        elif event_type == GlobalEventType.GOLDEN_RUSH:
            # Golden Rush: Golden Hash aparece 3× mais por 5 min (5× recompensa)
            # Aumenta chance de ser golden hash (30% ao invés de ~0.4%)
            if not is_golden and int(tx_metadata.get("word", "A")[:2], 16) % 100 < 30:
                tx_metadata["is_golden"] = True
                multiplier = 5.0
                tx_metadata["multiplier"] = multiplier

        elif event_type == GlobalEventType.MEMPOOL_FLOOD:
            # Mempool Flood: recompensas 2× por 10 min
            multiplier = multiplier * 2.0
            tx_metadata["multiplier"] = multiplier

        elif event_type == GlobalEventType.LIGHTNING_STORM:
            # Lightning Storm: 10× recompensa por 3 min
            multiplier = multiplier * 10.0
            tx_metadata["multiplier"] = multiplier

        return tx_metadata

    @staticmethod
    def get_event_grid_size(active_event_type: GlobalEventType | None = None) -> int:
        """Retorna o tamanho da grade com base no evento ativo.

        Args:
            active_event_type: Tipo de evento global ativo, ou None.

        Returns:
            Tamanho da grade (8, 12 ou 15).
        """
        if active_event_type == GlobalEventType.LIGHTNING_STORM:
            return 8  # 8×8 grid para Lightning Storm
        if active_event_type == GlobalEventType.MEMPOOL_FLOOD:
            return 15  # 15×15 grid obrigatório para Mempool Flood
        return 12  # padrão

    @staticmethod
    def get_event_time_limit(active_event_type: GlobalEventType | None = None, base_time: int = 60) -> int:
        """Retorna o tempo limite da rodada com base no evento ativo.

        Args:
            active_event_type: Tipo de evento global ativo, ou None.
            base_time: Tempo base em segundos.

        Returns:
            Tempo limite ajustado.
        """
        if active_event_type == GlobalEventType.LIGHTNING_STORM:
            return 20  # Ultra rápido para Lightning Storm
        if active_event_type == GlobalEventType.MEMPOOL_FLOOD:
            return base_time + 15  # Mais tempo para grade 15×15
        return base_time

    async def get_mempool_size(self) -> int | None:
        """Retorna o total de transações no mempool informado pelo nó.

        Returns:
            Quantidade de transações, ou ``None`` quando o RPC falha.
        """
        result = await self._rpc_call("getmempoolinfo", [])
        if not isinstance(result, dict):
            return None
        size = result.get("size")
        return int(size) if isinstance(size, (int, float)) and size >= 0 else None

    async def get_blockchain_info(self) -> dict[str, Any] | None:
        """Retorna sincronização e pruning informados pelo nó.

        Returns:
            Dict com ``chain``, ``initialblockdownload``, ``blocks``, ``headers``,
            ``verificationprogress``, ``pruned``, ou ``None`` quando o RPC falha.
        """
        result = await self._rpc_call("getblockchaininfo", [])
        return result if isinstance(result, dict) else None

    async def get_best_block_hash(self) -> str | None:
        """Obtém o hash da ponta atual para compor a epoch do stream.

        Returns:
            Hash hex do melhor bloco, ou ``None`` quando o RPC falha.
        """
        result = await self._rpc_call("getbestblockhash", [])
        return result if isinstance(result, str) and result else None

    async def validate_declared_network(
        self,
        max_attempts: int = 20,
        backoff_base: float = 3.0,
        max_delay: float = 60.0,
    ) -> dict[str, Any]:
        """Falha se o RPC conectado pertencer a outra chain.

        Compara ``getblockchaininfo.chain`` com a rede declarada em ``self.config``.
        Útil para detectar configuração incorreta no início do ingestor.

        Durante IBD (Initial Block Download), o Bitcoin Core pode não responder RPC
        por vários minutos. Este método faz retry com backoff exponencial (capado)
        para tolerar esse período — mas ainda falha se a chain estiver divergente.

        Args:
            max_attempts: Número máximo de tentativas (default 20).
            backoff_base: Intervalo base em segundos, dobrado a cada tentativa.
            max_delay: Teto máximo do delay em segundos (default 60s).

        Returns:
            Info do blockchain se a chain estiver correta.

        Raises:
            RuntimeError: Se o RPC estiver indisponível após todas as tentativas
                ou a chain estiver divergente.
        """
        import asyncio as _asyncio

        last_exc: Exception | None = None
        for attempt in range(1, max_attempts + 1):
            info = await self.get_blockchain_info()
            if info is not None:
                actual_chain = info.get("chain")
                expected_chain = self.config.network.rpc_chain
                if actual_chain != expected_chain:
                    raise RuntimeError(
                        f"Chain RPC divergente em {self.config.node_id}: "
                        f"esperada={expected_chain}, recebida={actual_chain}"
                    )
                in_ibd = bool(info.get("initialblockdownload", True))
                if in_ibd:
                    logger.warning(
                        "Nó %s em IBD (progresso=%.1f%%) — aguardando sync",
                        self.config.node_id,
                        float(info.get("verificationprogress", 0)) * 100,
                    )
                else:
                    logger.info(
                        "Nó %s validado: chain=%s blocks=%s",
                        self.config.node_id,
                        actual_chain,
                        info.get("blocks"),
                    )
                return info

            last_exc = Exception("getblockchaininfo retornou None")
            delay = min(backoff_base * (2 ** (attempt - 1)), max_delay)
            logger.warning(
                "RPC indisponível para %s (tentativa %d/%d); "
                "retry em %.0fs — IBD pode estar em andamento",
                self.config.node_id,
                attempt,
                max_attempts,
                delay,
            )
            await asyncio.sleep(delay)

        raise RuntimeError(
            f"RPC indisponível para o nó {self.config.node_id} "
            f"após {max_attempts} tentativas"
        )

    async def close(self) -> None:
        """Libera o pool HTTP utilizado nas chamadas RPC.

        Operação idempotente — pode ser chamada múltiplas vezes sem efeito colateral.
        """
        if self._owns_http_client:
            await self.http_client.aclose()
