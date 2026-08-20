"""Eventos globais do Mempool Miner.

Scheduler que dispara eventos periodicamente, broadcast via Redis Pub/Sub
para todos os clientes do realm. 4 tipos de evento:

- Fee Spike:     Todas as palavras são High Fee por 10 min (3× recompensa)
- Golden Rush:   Golden Hash aparece 3× mais por 5 min (5× recompensa)
- Mempool Flood: Grade 15×15 obrigatória, recompensas 2× por 10 min
- Lightning Storm: Lightning Mode ativo para todos por 3 min (10×, 8×8 grid)

O scheduler roda em cada instância do backend; o Redis lock garante que
apenas uma instância dispare cada evento.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

import redis.asyncio as redis

from app.events import event_envelope
from app.storage import events_channel

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tipos de evento
# ---------------------------------------------------------------------------

class GlobalEventType(str, Enum):
    FEE_SPIKE = "fee_spike"
    GOLDEN_RUSH = "golden_rush"
    MEMPOOL_FLOOD = "mempool_flood"
    LIGHTNING_STORM = "lightning_storm"


# Mapeamento de ícones e cores por tipo (usando variáveis CSS existentes)
EVENT_META: dict[GlobalEventType, dict[str, str]] = {
    GlobalEventType.FEE_SPIKE: {
        "icon": "⚡",
        "label": "Fee Spike",
        "description": "Todas as palavras são High Fee! 3× recompensa por 10 min.",
        "color": "#a855f7",  # --high-fee
    },
    GlobalEventType.GOLDEN_RUSH: {
        "icon": "🌟",
        "label": "Golden Rush",
        "description": "Golden Hash 3× mais frequente! 5× recompensa por 5 min.",
        "color": "#eab308",  # --golden-hash
    },
    GlobalEventType.MEMPOOL_FLOOD: {
        "icon": "🌊",
        "label": "Mempool Flood",
        "description": "Grade 15×15 obrigatória! Recompensas 2× por 10 min.",
        "color": "#f97316",  # --warning-orange
    },
    GlobalEventType.LIGHTNING_STORM: {
        "icon": "⛈️",
        "label": "Lightning Storm",
        "description": "Lightning Mode ativo! 10× recompensa, 8×8 grid por 3 min.",
        "color": "#0ea5e9",  # --lightning-blue
    },
}


# Durações em segundos
EVENT_DURATION_SECONDS: dict[GlobalEventType, int] = {
    GlobalEventType.FEE_SPIKE: 600,       # 10 min
    GlobalEventType.GOLDEN_RUSH: 300,     # 5 min
    GlobalEventType.MEMPOOL_FLOOD: 600,   # 10 min
    GlobalEventType.LIGHTNING_STORM: 180, # 3 min
}

# Tempo de aviso antecipado (2 minutos antes)
EVENT_PREANNOUNCE_SECONDS = 120


# ---------------------------------------------------------------------------
# Dados do evento
# ---------------------------------------------------------------------------

@dataclass
class GlobalEvent:
    """Representa um evento global ativo ou próximo."""

    event_type: GlobalEventType
    realm_id: str
    started_at: str  # ISO 8601
    ends_at: str     # ISO 8601
    preannounced: bool = False
    # Contagem de blocos/mineradores afetados (rastreamento)
    blocks_affected: int = 0
    players_affected: int = 0


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class GlobalEventScheduler:
    """Scheduler que dispara eventos globais periodicamente.

    Usa um lock Redis (SET NX) para garantir que apenas uma instância
    do backend dispare eventos em um dado realm.

    Ciclo:
    1. Aguarda intervalo aleatório entre 30-60 minutos.
    2. Escolhe um tipo de evento aleatório.
    3. Pre-anuncia 2 minutos antes (via Redis Pub/Sub).
    4. Dispara o evento (via Redis Pub/Sub).
    5. Após a duração, encerra o evento.
    6. Repete.
    """

    def __init__(
        self,
        redis_client: redis.Redis,
        realm_id: str,
        min_interval_seconds: int = 30 * 60,   # 30 min
        max_interval_seconds: int = 60 * 60,   # 60 min
    ) -> None:
        self.redis_client = redis_client
        self.realm_id = realm_id
        self.min_interval = min_interval_seconds
        self.max_interval = max_interval_seconds
        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._active_event: GlobalEvent | None = None
        self._lock_key = f"mempool_miner:v2:{{{realm_id}}}:global_event_lock"
        self._lock_ttl = max_interval_seconds + 60  # TTL maior que o intervalo máximo

    async def start(self) -> None:
        """Inicia o scheduler em background."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(
            self._loop(),
            name=f"global-event-scheduler-{self.realm_id}",
        )
        logger.info(
            "Scheduler de eventos globais iniciado para %s "
            "(intervalo %ds-%ds)",
            self.realm_id,
            self.min_interval,
            self.max_interval,
        )

    async def stop(self) -> None:
        """Para o scheduler."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        logger.info("Scheduler de eventos globais encerrado para %s", self.realm_id)

    async def _loop(self) -> None:
        """Loop principal do scheduler."""
        while self._running:
            try:
                await self._run_cycle()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Erro no scheduler de eventos globais %s", self.realm_id)
                # Espera 1 minuto antes de tentar novamente
                await asyncio.sleep(60)

    async def _run_cycle(self) -> None:
        """Executa um ciclo completo: aguarda -> escolhe -> dispara -> encerra."""
        # Aguarda intervalo aleatório
        interval = random.randint(self.min_interval, self.max_interval)
        logger.info(
            "Aguardando %ds até próximo evento global em %s",
            interval,
            self.realm_id,
        )
        if await self._wait_with_cancel(interval):
            return

        # Tenta adquirir lock Redis
        acquired = await self.redis_client.set(
            self._lock_key,
            "1",
            nx=True,
            ex=self._lock_ttl,
        )
        if not acquired:
            logger.debug(
                "Lock de evento global não adquirido para %s — outra instância está rodando",
                self.realm_id,
            )
            return

        try:
            # Escolhe tipo de evento aleatório
            event_type = random.choice(list(GlobalEventType))
            await self._trigger_event(event_type)
        finally:
            # Libera lock
            await self.redis_client.delete(self._lock_key)

    async def _wait_with_cancel(self, seconds: int) -> bool:
        """Aguarda segundos, retorna True se cancelado."""
        try:
            await asyncio.sleep(seconds)
            return False
        except asyncio.CancelledError:
            return True

    async def _trigger_event(self, event_type: GlobalEventType) -> None:
        """Dispara um evento global: pre-anúncio -> evento -> encerramento."""
        duration = EVENT_DURATION_SECONDS[event_type]
        meta = EVENT_META[event_type]
        now = datetime.now(UTC)
        started_at = now.isoformat()
        ends_at = (now + timedelta(seconds=duration)).isoformat()

        event = GlobalEvent(
            event_type=event_type,
            realm_id=self.realm_id,
            started_at=started_at,
            ends_at=ends_at,
        )
        self._active_event = event

        # 1. Pre-anúncio (2 minutos antes)
        preannounce_at = (now + timedelta(seconds=duration - EVENT_PREANNOUNCE_SECONDS)).isoformat()
        await self._publish_event(
            event_type=event_type,
            action="event_preannounce",
            started_at=started_at,
            ends_at=ends_at,
            preannounced=True,
            meta=meta,
        )
        logger.info(
            "Pré-anúncio de evento global %s em %s às %s",
            meta["label"],
            self.realm_id,
            preannounce_at,
        )

        # 2. Aguarda até o momento do evento
        wait_before = duration - EVENT_PREANNOUNCE_SECONDS
        if await self._wait_with_cancel(wait_before):
            return

        # 3. Dispara o evento
        await self._publish_event(
            event_type=event_type,
            action="event_started",
            started_at=started_at,
            ends_at=ends_at,
            preannounced=False,
            meta=meta,
        )
        logger.info(
            "Evento global %s iniciado em %s — dura até %s",
            meta["label"],
            self.realm_id,
            ends_at,
        )

        # 4. Aguarda duração do evento
        if await self._wait_with_cancel(duration):
            return

        # 5. Encerra o evento
        await self._publish_event(
            event_type=event_type,
            action="event_ended",
            started_at=started_at,
            ends_at=ends_at,
            preannounced=False,
            meta=meta,
        )
        logger.info(
            "Evento global %s encerrado em %s",
            meta["label"],
            self.realm_id,
        )
        self._active_event = None

    async def _publish_event(
        self,
        *,
        event_type: GlobalEventType,
        action: str,
        started_at: str,
        ends_at: str,
        preannounced: bool,
        meta: dict[str, str],
    ) -> None:
        """Publica um evento no canal Pub/Sub do realm."""
        channel = events_channel(self.realm_id)
        payload = {
            "schema_version": 2,
            "event_id": f"global_event:{self.realm_id}:{event_type.value}:{action}",
            "action": action,
            "node_id": "scheduler",
            "network": "mempool_miner",
            "chain": "mempool_miner",
            "realm_id": self.realm_id,
            "observed_at": datetime.now(UTC).isoformat(),
            "source_session": None,
            "source_sequence": None,
            "epoch": None,
            # Campos específicos do evento global
            "event_type": event_type.value,
            "event_label": meta["label"],
            "event_icon": meta["icon"],
            "event_description": meta["description"],
            "event_color": meta["color"],
            "event_preannounced": preannounced,
            "event_started_at": started_at,
            "event_ends_at": ends_at,
        }
        try:
            await self.redis_client.publish(channel, json.dumps(payload))
            # Atualiza status do evento para consulta rápida
            await publish_event_status(self.redis_client, self.realm_id, payload)
        except Exception:
            logger.exception("Falha ao publicar evento global %s", action)


# ---------------------------------------------------------------------------
# Utilitários para consulta de estado do evento
# ---------------------------------------------------------------------------

async def get_active_event(
    redis_client: redis.Redis,
    realm_id: str,
) -> dict[str, Any] | None:
    """Verifica se há um evento global ativo ou próximo no realm.

    Lê o último evento publicado no canal Pub/Sub do realm.
    Retorna None se não houver evento relevante.
    """
    channel = events_channel(realm_id)
    # Usa um canal de status separado para consulta rápida
    status_key = f"mempool_miner:v2:{{{realm_id}}}:global_event_status"
    raw = await redis_client.get(status_key)
    if not raw:
        return None
    import json
    try:
        status = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None

    # Verifica se o evento ainda está ativo ou próximo
    from datetime import datetime as _dt
    ends_at = status.get("event_ends_at")
    if ends_at:
        try:
            end_time = _dt.fromisoformat(ends_at)
            now = _dt.now(UTC)
            if end_time <= now:
                # Evento expirado — limpa
                await redis_client.delete(status_key)
                return None
        except (ValueError, TypeError):
            pass

    return status


async def publish_event_status(
    redis_client: redis.Redis,
    realm_id: str,
    event_data: dict[str, Any],
) -> None:
    """Publica o status do evento global para consulta rápida."""
    status_key = f"mempool_miner:v2:{{{realm_id}}}:global_event_status"
    import json
    await redis_client.set(status_key, json.dumps(event_data), ex=7200)  # TTL 2h
