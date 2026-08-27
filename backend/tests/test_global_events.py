"""Testes de regressão do scheduler de eventos globais (Fase 3.2)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from app.global_events import (
    EVENT_DURATION_SECONDS,
    EVENT_PREANNOUNCE_SECONDS,
    GlobalEventScheduler,
    GlobalEventType,
)


@pytest.mark.asyncio
async def test_trigger_event_preannounce_timing() -> None:
    """Fase 3.2: o pre-anúncio deve sair AGORA, com started_at = now + 120s.

    Antes da correção, o pre-anúncio era publicado no mesmo instante do
    trigger com started_at = now (janela de pre-anúncio errada) e o
    scheduler aguardava ``duration - 120s`` até publicar event_started.
    Agora: preannounce agora → aguarda 120s → started → aguarda duration →
    ended, com started_at/ends_at refletindo o início/fim reais.
    """
    scheduler = GlobalEventScheduler(redis_client=AsyncMock(), realm_id="regtest")

    published: list[dict[str, object]] = []
    waits: list[int] = []

    async def fake_publish(
        *,
        event_type: GlobalEventType,
        action: str,
        started_at: str,
        ends_at: str,
        preannounced: bool,
        meta: dict[str, str],
    ) -> None:
        published.append(
            {
                "action": action,
                "started_at": started_at,
                "ends_at": ends_at,
                "preannounced": preannounced,
            }
        )

    async def fake_wait(seconds: int) -> bool:
        waits.append(seconds)
        return False  # nunca cancelado

    scheduler._publish_event = fake_publish
    scheduler._wait_with_cancel = fake_wait

    before = datetime.now(UTC)
    await scheduler._trigger_event(GlobalEventType.FEE_SPIKE)
    after = datetime.now(UTC)

    duration = EVENT_DURATION_SECONDS[GlobalEventType.FEE_SPIKE]

    # 1. Sequência de ações correta.
    assert [p["action"] for p in published] == [
        "event_preannounce",
        "event_started",
        "event_ended",
    ]

    # 2. Pre-anúncio: publicado agora, com started_at ≈ now + 120s.
    pre = published[0]
    assert pre["preannounced"] is True
    pre_started = datetime.fromisoformat(str(pre["started_at"]))
    assert pre_started > before + timedelta(seconds=EVENT_PREANNOUNCE_SECONDS - 5)
    assert pre_started < after + timedelta(seconds=EVENT_PREANNOUNCE_SECONDS + 5)

    # 3. started/ended compartilham o MESMO started_at/ends_at (início/fim reais).
    started = published[1]
    ended = published[2]
    assert started["started_at"] == pre["started_at"]
    assert ended["started_at"] == pre["started_at"]
    assert started["ends_at"] == pre["ends_at"]
    assert ended["ends_at"] == pre["ends_at"]
    assert started["preannounced"] is False
    assert ended["preannounced"] is False

    # 4. ends_at = started_at + duration.
    ends = datetime.fromisoformat(str(pre["ends_at"]))
    assert ends == pre_started + timedelta(seconds=duration)

    # 5. Janelas de espera: 120s (pre-anúncio) e duration (evento ativo).
    assert waits == [EVENT_PREANNOUNCE_SECONDS, duration]


@pytest.mark.asyncio
async def test_get_active_event_ignores_preannounce_by_default() -> None:
    """Fase 3.2 (ponta solta ALTO): o ingestor só aplica efeitos no evento ativo.

    ``get_active_event`` com o padrão (``include_preannounce=False``) deve
    retornar ``None`` durante a janela de pre-anúncio (``now < started_at``)
    e o status durante o evento ativo. Antes da correção, a função ignorava
    ``started_at`` e o ingestor aplicava ``apply_event_effects`` 120s antes
    do início real.
    """
    from app.global_events import get_active_event

    now = datetime.now(UTC)
    status = {
        "event_type": "fee_spike",
        "event_started_at": (now + timedelta(seconds=60)).isoformat(),
        "event_ends_at": (now + timedelta(seconds=660)).isoformat(),
        "event_preannounced": True,
    }

    redis_client = AsyncMock()
    redis_client.get.return_value = json.dumps(status)

    # Durante o pre-anúncio: None no padrão (ingestor não aplica efeitos).
    assert await get_active_event(redis_client, "regtest") is None
    # Com include_preannounce=True: o endpoint REST vê o pre-anúncio (banner).
    assert await get_active_event(
        redis_client, "regtest", include_preannounce=True
    ) == status


@pytest.mark.asyncio
async def test_get_active_event_returns_status_when_active() -> None:
    """Evento ativo (started_at <= now < ends_at) é retornado nos dois modos."""
    from app.global_events import get_active_event

    now = datetime.now(UTC)
    status = {
        "event_type": "golden_rush",
        "event_started_at": (now - timedelta(seconds=30)).isoformat(),
        "event_ends_at": (now + timedelta(seconds=270)).isoformat(),
        "event_preannounced": False,
    }

    redis_client = AsyncMock()
    redis_client.get.return_value = json.dumps(status)

    assert await get_active_event(redis_client, "regtest") == status
    assert await get_active_event(
        redis_client, "regtest", include_preannounce=True
    ) == status


@pytest.mark.asyncio
async def test_get_active_event_clears_expired_status() -> None:
    """Evento expirado (ends_at <= now) limpa a status key e retorna None."""
    from app.global_events import get_active_event

    now = datetime.now(UTC)
    status = {
        "event_type": "lightning_storm",
        "event_started_at": (now - timedelta(seconds=300)).isoformat(),
        "event_ends_at": (now - timedelta(seconds=30)).isoformat(),
        "event_preannounced": False,
    }

    redis_client = AsyncMock()
    redis_client.get.return_value = json.dumps(status)

    assert await get_active_event(redis_client, "regtest") is None
    redis_client.delete.assert_awaited_once()
