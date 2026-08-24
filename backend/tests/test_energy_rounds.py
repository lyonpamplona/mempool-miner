"""Contratos de idempotência e compensação do sistema de energia."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from app import main as main_module
from fastapi import HTTPException

ROUND_ID = "123e4567-e89b-12d3-a456-426614174000"


@pytest.mark.asyncio
async def test_spend_energy_is_idempotent_for_the_same_round(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Repetir o mesmo round_id não pode debitar energia duas vezes."""
    redis_client = AsyncMock()
    redis_client.eval.side_effect = ([1, 9], [0, 9])
    monkeypatch.setattr(main_module, "redis_client", redis_client)

    first = await main_module.spend_energy("regtest", "MinerQA", ROUND_ID)
    second = await main_module.spend_energy("regtest", "MinerQA", ROUND_ID)

    assert first == {
        "username": "MinerQA",
        "round_id": ROUND_ID,
        "current": 9,
        "charged": True,
    }
    assert second == {
        "username": "MinerQA",
        "round_id": ROUND_ID,
        "current": 9,
        "charged": False,
    }
    assert redis_client.eval.await_count == 2
    first_call = redis_client.eval.await_args_list[0]
    second_call = redis_client.eval.await_args_list[1]
    assert first_call.args[:4] == second_call.args[:4]


@pytest.mark.asyncio
async def test_refund_energy_is_idempotent_for_the_same_round(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Compensar o mesmo round_id duas vezes deve devolver no máximo 1 energia."""
    redis_client = AsyncMock()
    redis_client.eval.side_effect = ([1, 10], [0, 10])
    monkeypatch.setattr(main_module, "redis_client", redis_client)

    first = await main_module.refund_energy("regtest", "MinerQA", ROUND_ID)
    second = await main_module.refund_energy("regtest", "MinerQA", ROUND_ID)

    assert first == {
        "username": "MinerQA",
        "round_id": ROUND_ID,
        "current": 10,
        "refunded": True,
    }
    assert second == {
        "username": "MinerQA",
        "round_id": ROUND_ID,
        "current": 10,
        "refunded": False,
    }
    assert redis_client.eval.await_count == 2


@pytest.mark.asyncio
async def test_energy_round_rejects_non_uuid_identifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """round_id arbitrário não pode virar parte de uma chave Redis."""
    redis_client = AsyncMock()
    monkeypatch.setattr(main_module, "redis_client", redis_client)

    with pytest.raises(HTTPException) as exc_info:
        await main_module.spend_energy("regtest", "MinerQA", "../../invalid")

    assert exc_info.value.status_code == 422
    redis_client.eval.assert_not_awaited()


@pytest.mark.asyncio
async def test_buy_energy_debits_balance_and_adds_energy_atomically(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Compras concorrentes não podem sobrescrever saldo ou energia."""
    redis_client = AsyncMock()
    redis_client.eval.return_value = [1, 6, 8000]
    redis_client.hgetall.side_effect = [
        {"balance": "10000"},
        {"current": "3", "max": "10", "last_refill": "4102444800"},
    ]
    monkeypatch.setattr(main_module, "redis_client", redis_client)

    result = await main_module.buy_energy("regtest", "MinerQA")

    assert result == {"username": "MinerQA", "current": 6, "balance": 8000}
    redis_client.eval.assert_awaited_once()
    eval_args = redis_client.eval.await_args.args
    assert eval_args[1] == 2
    assert main_module.player_state_key("regtest", "MinerQA") in eval_args[2:4]
    assert main_module.energy_key("regtest", "MinerQA") in eval_args[2:4]
    redis_client.hgetall.assert_not_awaited()
    redis_client.hset.assert_not_awaited()
