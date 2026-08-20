"""Regressões dos contratos REST corrigidos na Fase 2."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from app import main as main_module
from app import season_pass



def _key(realm_id: str, username: str) -> str:
    return f"test:{realm_id}:{username}"


def _definition(realm_id: str) -> SimpleNamespace:
    return SimpleNamespace(realm_id=realm_id)


@pytest.mark.asyncio
async def test_season_data_awaits_async_redis() -> None:
    """Season Pass deve consumir o resultado do Redis, não o objeto coroutine."""
    redis_client = AsyncMock()
    redis_client.hgetall.return_value = {}

    result = await season_pass.get_season_data(
        "signet",
        "Miner",
        _key,
        _key,
        _key,
        redis_client,
        _definition,
    )

    assert result["level"] == 0
    redis_client.hgetall.assert_awaited_once_with("test:signet:Miner")


@pytest.mark.asyncio
async def test_season_claim_uses_one_atomic_redis_script() -> None:
    """Validar, creditar e marcar claim deve ocorrer em uma única operação Redis."""
    redis_client = AsyncMock()
    redis_client.eval.return_value = "ok"

    result = await season_pass.claim_season_reward(
        "signet",
        "Miner",
        1,
        _key,
        _key,
        _key,
        redis_client,
        _definition,
    )

    assert result == {
        "reward": season_pass.SEASON_FREE_REWARDS[1],
        "claimed_level": 1,
    }
    redis_client.eval.assert_awaited_once()
    redis_client.hgetall.assert_not_awaited()
    redis_client.hget.assert_not_awaited()
    redis_client.hincrby.assert_not_awaited()
    redis_client.hset.assert_not_awaited()


@pytest.mark.asyncio
async def test_season_premium_purchase_uses_one_atomic_redis_script() -> None:
    """Saldo e acesso premium devem ser alterados pela mesma operação Redis."""
    redis_client = AsyncMock()
    redis_client.eval.return_value = "ok"

    result = await season_pass.buy_season_premium(
        "signet",
        "Miner",
        _key,
        _key,
        _key,
        redis_client,
        _definition,
    )

    assert result == {"is_premium": True, "cost": 50000}
    redis_client.eval.assert_awaited_once()
    redis_client.hget.assert_not_awaited()
    redis_client.hincrby.assert_not_awaited()
    redis_client.hset.assert_not_awaited()


@pytest.mark.asyncio
async def test_market_list_uses_supported_zrange_signature(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Listagem do mercado não pode duplicar os argumentos start/end."""

    class StrictRedis:
        async def zrange(
            self,
            key: str,
            start: int,
            end: int,
            *,
            withscores: bool = False,
        ) -> list[tuple[str, float]]:
            assert key
            assert start == 0
            assert end == 4
            assert withscores is True
            return []

    monkeypatch.setattr(main_module, "redis_client", StrictRedis())

    assert await main_module._list_market("signet", limit=5) == []


@pytest.mark.asyncio
async def test_market_sell_uses_one_atomic_redis_script(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Consumo do inventário e publicação do listing devem ser indivisíveis."""
    redis_client = AsyncMock()
    redis_client.eval.return_value = "ok"
    monkeypatch.setattr(main_module, "redis_client", redis_client)

    result = await main_module.sell_on_market(
        "regtest",
        main_module.MarketSellRequest(
            username="Miner",
            powerup_id="scanner",
            price=1000,
        ),
    )

    assert result["status"] == "listed"
    redis_client.eval.assert_awaited_once()
    redis_client.hgetall.assert_not_awaited()
    redis_client.hset.assert_not_awaited()
    redis_client.zadd.assert_not_awaited()


@pytest.mark.asyncio
async def test_market_sell_does_not_publish_unsold_listing_to_sales_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Histórico de vendas deve ser preenchido somente após uma compra concluída."""
    redis_client = AsyncMock()
    redis_client.eval.return_value = "ok"
    monkeypatch.setattr(main_module, "redis_client", redis_client)

    await main_module.sell_on_market(
        "regtest",
        main_module.MarketSellRequest(
            username="Miner",
            powerup_id="scanner",
            price=1000,
        ),
    )

    eval_args = redis_client.eval.await_args.args
    key_count = eval_args[1]
    script_keys = eval_args[2 : 2 + key_count]
    assert main_module.market_history_key("regtest") not in script_keys
    assert "history_key" not in eval_args[0]


@pytest.mark.asyncio
async def test_market_purchase_keeps_escrowed_seller_inventory_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Comprar não pode remover outra unidade do vendedor após o escrow no sell."""
    listing = {
        "seller": "Seller",
        "powerup_id": "scanner",
        "price": 1000,
    }
    redis_client = AsyncMock()
    redis_client.zpopmin.return_value = [(json.dumps(listing), 1000.0)]
    redis_client.hget.return_value = "2000"
    redis_client.eval.return_value = "ok"
    monkeypatch.setattr(main_module, "redis_client", redis_client)

    result = await main_module.buy_from_market(
        "regtest",
        main_module.MarketBuyRequest(username="Buyer"),
    )

    assert result["status"] == "purchased"
    eval_args = redis_client.eval.await_args.args
    key_count = eval_args[1]
    script_keys = eval_args[2 : 2 + key_count]
    assert main_module.powerups_key("regtest", "Seller") not in script_keys
    assert "powerups_seller" not in eval_args[0]


def test_stats_update_accepts_fields_used_by_daily_missions() -> None:
    """Campos consumidos pelo motor de missões devem pertencer ao contrato."""
    payload = main_module.StatsUpdate(
        username="Miner",
        rbf_used=1,
        max_round_earnings=50000,
    )

    assert payload.rbf_used == 1
    assert payload.max_round_earnings == 50000


