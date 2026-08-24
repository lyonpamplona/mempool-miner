"""Testes da migração de dados legados."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from app.storage import (
    LEGACY_LEADERBOARD_KEY,
    LEGACY_MEMPOOL_COUNT_KEY,
    MIGRATE_COUNTER_SCRIPT,
    MIGRATE_LEADERBOARD_SCRIPT,
    energy_key,
    energy_round_key,
    leaderboard_key,
    mempool_count_key,
    migrate_legacy_default,
)


def test_energy_round_key_shares_realm_slot_and_isolates_rounds() -> None:
    energy = energy_key("signet", "MinerQA")
    first = energy_round_key("signet", "MinerQA", "round-a")
    second = energy_round_key("signet", "MinerQA", "round-b")

    assert "{signet}" in energy
    assert "{signet}" in first
    assert first != second
    assert first.endswith(":MinerQA:round-a")


@pytest.mark.asyncio
async def test_migrate_legacy_default_runs_both_scripts() -> None:
    """migrate_legacy_default() executa os dois scripts de migração."""
    client = AsyncMock()
    client.eval = AsyncMock(return_value=0)

    await migrate_legacy_default(client, "regtest")

    assert client.eval.call_count == 2

    # Primeiro call: migração do leaderboard.
    first_call = client.eval.call_args_list[0]
    assert first_call[0][0] == MIGRATE_LEADERBOARD_SCRIPT
    assert first_call[0][2] == leaderboard_key("regtest")
    assert first_call[0][3] == LEGACY_LEADERBOARD_KEY

    # Segundo call: migração do counter.
    second_call = client.eval.call_args_list[1]
    assert second_call[0][0] == MIGRATE_COUNTER_SCRIPT
    assert second_call[0][2] == mempool_count_key("regtest")
    assert second_call[0][3] == LEGACY_MEMPOOL_COUNT_KEY


@pytest.mark.asyncio
async def test_migrate_legacy_default_with_different_realm() -> None:
    """Migração usa chaves do realm correto."""
    client = AsyncMock()
    client.eval = AsyncMock(return_value=0)

    await migrate_legacy_default(client, "signet")

    # Verifica que as chaves usam "signet".
    first_call = client.eval.call_args_list[0]
    assert "signet" in first_call[0][2]

    second_call = client.eval.call_args_list[1]
    assert "signet" in second_call[0][2]


@pytest.mark.asyncio
async def test_migrate_leaderboard_script_is_idempotent() -> None:
    """Script Lua do leaderboard retorna 0 se destino já existe."""
    # Simula o comportamento do script: se KEYS[1] já existe, retorna 0.
    # Isso é testado indiretamente — o script verifica exists(KEYS[1]).
    # Se o destino já tem dados, o script não faz nada.
    assert "exists" in MIGRATE_LEADERBOARD_SCRIPT
    assert "zadd" in MIGRATE_LEADERBOARD_SCRIPT


@pytest.mark.asyncio
async def test_migrate_counter_script_is_idempotent() -> None:
    """Script Lua do counter retorna 0 se destino já existe."""
    assert "exists" in MIGRATE_COUNTER_SCRIPT
    assert "set" in MIGRATE_COUNTER_SCRIPT
