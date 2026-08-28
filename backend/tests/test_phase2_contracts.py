"""Regressões dos contratos REST corrigidos na Fase 2."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from app import main as main_module
from app import season_pass


def _key(realm_id: str, username: str) -> str:
    return f"test:{realm_id}:{username}"


def _card_detail_key(realm_id: str, username: str, card_id: str) -> str:
    return f"test:{realm_id}:{username}:card:{card_id}"


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
    # Fase 5.5: get_season_data chama ensure_season_rollover (hgetall + hset +
    # expire) e depois lê o estado (hgetall) — 2 chamadas de hgetall.
    assert redis_client.hgetall.await_count == 2
    redis_client.hgetall.assert_awaited_with("test:signet:Miner")
    # O rollover grava o season_id atual na chave.
    redis_client.hset.assert_awaited()


@pytest.mark.asyncio
async def test_season_claim_uses_one_atomic_redis_script() -> None:
    """Validar, creditar e marcar claim deve ocorrer em uma única operação Redis.

    Fase 5.5: o rollover (ensure_season_rollover) roda antes do script —
    hgetall + hset(season_id) + expire. O crédito em si continua atômico
    (um único eval).
    """
    redis_client = AsyncMock()
    redis_client.eval.return_value = "ok"
    redis_client.hgetall.return_value = {}

    result = await season_pass.claim_season_reward(
        "signet",
        "Miner",
        1,
        _key,
        _key,
        _key,
        _key,
        _card_detail_key,
        redis_client,
        _definition,
    )

    assert result["reward"] == season_pass.SEASON_FREE_REWARDS[1]
    assert result["claimed_level"] == 1
    redis_client.eval.assert_awaited_once()
    # Rollover: 1 hgetall (estado) + 1 hset (season_id) + 1 expire.
    assert redis_client.hgetall.await_count == 1
    assert redis_client.hset.await_count == 1
    redis_client.hget.assert_not_awaited()
    redis_client.hincrby.assert_not_awaited()


@pytest.mark.asyncio
async def test_season_premium_purchase_uses_one_atomic_redis_script() -> None:
    """Saldo e acesso premium devem ser alterados pela mesma operação Redis.

    Fase 5.5: o rollover roda antes (hgetall + hset season_id + expire) e
    bloqueia a compra em temporada encerrada. O débito/ativação continua
    atômico (um único eval).
    """
    redis_client = AsyncMock()
    redis_client.eval.return_value = "ok"
    redis_client.hgetall.return_value = {}

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
    # Rollover: 1 hgetall + 1 hset (season_id).
    assert redis_client.hgetall.await_count == 1
    assert redis_client.hset.await_count == 1
    redis_client.hget.assert_not_awaited()
    redis_client.hincrby.assert_not_awaited()


@pytest.mark.asyncio
async def test_powerup_buy_uses_server_price_and_atomic_script(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Compra direta deve debitar e creditar em um único EVAL."""
    redis_client = AsyncMock()
    redis_client.eval.return_value = [1, 95000, 1, 1]
    redis_client.hgetall.return_value = {"scanner": "1"}
    monkeypatch.setattr(main_module, "redis_client", redis_client)

    request = main_module.PowerupBuyRequest(
        username="Miner",
        powerup_id="scanner",
        quantity=1,
        tx_id="buy-pu-scanner-001",
    )
    result = await main_module.buy_powerup("regtest", request)

    assert result["status"] == "purchased"
    assert result["price"] == 5000
    assert result["total_cost"] == 5000
    assert result["balance"] == 95000
    assert result["inventory"]["scanner"] == 1
    redis_client.eval.assert_awaited_once()
    args = redis_client.eval.await_args.args
    assert args[1] == 4
    assert "5000" in args
    assert "scanner" in args
    assert any("buy-pu-scanner-001" in str(value) for value in args)
    redis_client.hset.assert_not_awaited()
    redis_client.hincrby.assert_not_awaited()


@pytest.mark.asyncio
async def test_powerup_buy_rejects_daily_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Limite diário deve ser decidido pelo resultado atômico do Redis."""
    redis_client = AsyncMock()
    redis_client.eval.return_value = [-2, 10000, 3, 3]
    monkeypatch.setattr(main_module, "redis_client", redis_client)

    with pytest.raises(main_module.HTTPException) as error:
        await main_module.buy_powerup(
            "regtest",
            main_module.PowerupBuyRequest(
                username="Miner",
                powerup_id="scanner",
                tx_id="buy-pu-scanner-limit",
            ),
        )

    assert error.value.status_code == 409
    redis_client.eval.assert_awaited_once()


def test_powerup_buy_payload_does_not_accept_client_price() -> None:
    """O cliente não pode alterar o preço de uma compra."""
    with pytest.raises(ValueError):
        main_module.PowerupBuyRequest(
            username="Miner",
            powerup_id="scanner",
            price=1,
            tx_id="buy-pu-price",
        )


@pytest.mark.asyncio
async def test_powerup_activation_uses_one_atomic_redis_script(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ativação deve decrementar inventário e timer no mesmo EVAL."""
    redis_client = AsyncMock()
    redis_client.eval.return_value = [1, 2]
    redis_client.hgetall.return_value = {"scanner": "2"}
    monkeypatch.setattr(main_module, "redis_client", redis_client)

    result = await main_module._activate_powerup("regtest", "Miner", "scanner")

    assert result["status"] == "activated"
    assert result["powerup_id"] == "scanner"
    redis_client.eval.assert_awaited_once()
    redis_client.hget.assert_not_awaited()
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
async def test_market_cancel_returns_powerup_atomically(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cancelar um listing próprio deve devolver o power-up ao inventário (Lua atômico)."""
    listing_id = "123e4567-e89b-12d3-a456-426614174000"
    member = json.dumps(
        {
            "listing_id": listing_id,
            "seller": "Miner",
            "powerup_id": "scanner",
            "powerup_name": "Scanner",
            "powerup_icon": "x",
            "price": 1000,
            "timestamp": "2026-08-24T00:00:00+00:00",
        },
        separators=(",", ":"),
    )
    redis_client = AsyncMock()
    redis_client.zrange.return_value = [(member, 1000.0)]
    redis_client.eval.return_value = "ok"
    monkeypatch.setattr(main_module, "redis_client", redis_client)

    result = await main_module.cancel_market_listing(
        "regtest",
        main_module.MarketCancelRequest(username="Miner", listing_id=listing_id),
    )

    assert result["status"] == "cancelled"
    assert result["powerup"] == "scanner"
    # A devolução deve ser atômica (1 único EVAL), sem hincrby separado.
    redis_client.eval.assert_awaited_once()
    redis_client.hincrby.assert_not_awaited()
    redis_client.zrem.assert_not_awaited()


@pytest.mark.asyncio
async def test_market_cancel_rejects_foreign_listing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cancelar listing de outro jogador deve retornar 403."""
    listing_id = "123e4567-e89b-12d3-a456-426614174000"
    member = json.dumps(
        {
            "listing_id": listing_id,
            "seller": "Outro",
            "powerup_id": "scanner",
            "powerup_name": "Scanner",
            "powerup_icon": "x",
            "price": 1000,
            "timestamp": "2026-08-24T00:00:00+00:00",
        },
        separators=(",", ":"),
    )
    redis_client = AsyncMock()
    redis_client.zrange.return_value = [(member, 1000.0)]
    monkeypatch.setattr(main_module, "redis_client", redis_client)

    with pytest.raises(main_module.HTTPException) as exc:
        await main_module.cancel_market_listing(
            "regtest",
            main_module.MarketCancelRequest(username="Miner", listing_id=listing_id),
        )
    assert exc.value.status_code == 403
    # Não deve chegar à transação atômica.
    redis_client.eval.assert_not_awaited()


@pytest.mark.asyncio
async def test_market_cancel_missing_listing_returns_404(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cancelar listing inexistente deve retornar 404."""
    redis_client = AsyncMock()
    redis_client.zrange.return_value = []
    monkeypatch.setattr(main_module, "redis_client", redis_client)

    with pytest.raises(main_module.HTTPException) as exc:
        await main_module.cancel_market_listing(
            "regtest",
            main_module.MarketCancelRequest(
                username="Miner",
                listing_id="123e4567-e89b-12d3-a456-426614174000",
            ),
        )
    assert exc.value.status_code == 404
    redis_client.eval.assert_not_awaited()


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
    listing_id = "123e4567-e89b-12d3-a456-426614174000"
    listing = {
        "listing_id": listing_id,
        "seller": "Seller",
        "powerup_id": "scanner",
        "price": 1000,
    }
    redis_client = AsyncMock()
    redis_client.zrange.return_value = [(json.dumps(listing), 1000.0)]
    redis_client.eval.return_value = "ok"
    monkeypatch.setattr(main_module, "redis_client", redis_client)

    result = await main_module.buy_from_market(
        "regtest",
        main_module.MarketBuyRequest(username="Buyer", listing_id=listing_id),
    )

    assert result["status"] == "purchased"
    eval_args = redis_client.eval.await_args.args
    key_count = eval_args[1]
    script_keys = eval_args[2 : 2 + key_count]
    assert main_module.powerups_key("regtest", "Seller") not in script_keys
    assert "powerups_seller" not in eval_args[0]


@pytest.mark.asyncio
async def test_market_purchase_selects_listing_and_removes_it_atomically(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Clique deve comprar o listing indicado sem janela de pop/rollback."""
    listing_id = "123e4567-e89b-12d3-a456-426614174000"
    other_listing = {
        "listing_id": "123e4567-e89b-12d3-a456-426614174001",
        "seller": "OtherSeller",
        "powerup_id": "magnet",
        "price": 500,
    }
    selected_listing = {
        "listing_id": listing_id,
        "seller": "SelectedSeller",
        "powerup_id": "scanner",
        "price": 1000,
    }
    redis_client = AsyncMock()
    redis_client.zrange.return_value = [
        (json.dumps(other_listing), 500.0),
        (json.dumps(selected_listing), 1000.0),
    ]
    redis_client.eval.return_value = "ok"
    monkeypatch.setattr(main_module, "redis_client", redis_client)

    result = await main_module.buy_from_market(
        "regtest",
        main_module.MarketBuyRequest(username="Buyer", listing_id=listing_id),
    )

    assert result["status"] == "purchased"
    assert result["seller"] == "SelectedSeller"
    redis_client.zpopmin.assert_not_awaited()
    redis_client.zadd.assert_not_awaited()
    eval_args = redis_client.eval.await_args.args
    key_count = eval_args[1]
    script_keys = eval_args[2 : 2 + key_count]
    assert main_module.market_list_key("regtest") in script_keys
    assert "zrem" in eval_args[0].lower()


@pytest.mark.asyncio
async def test_market_purchase_publishes_sale_event_for_online_seller(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Vendedor conectado deve receber listing e saldo atualizados via WS."""
    listing_id = "123e4567-e89b-12d3-a456-426614174000"
    listing = {
        "listing_id": listing_id,
        "seller": "Seller",
        "powerup_id": "scanner",
        "price": 1000,
    }
    redis_client = AsyncMock()
    redis_client.zrange.return_value = [(json.dumps(listing), 1000.0)]
    redis_client.eval.return_value = "ok"
    monkeypatch.setattr(main_module, "redis_client", redis_client)

    await main_module.buy_from_market(
        "regtest",
        main_module.MarketBuyRequest(username="Buyer", listing_id=listing_id),
    )

    redis_client.publish.assert_awaited_once()
    channel, raw_event = redis_client.publish.await_args.args
    event = json.loads(raw_event)
    assert channel == main_module.events_channel("regtest")
    assert event["action"] == "market_sale"
    assert event["realm_id"] == "regtest"
    assert event["listing_id"] == listing_id
    assert event["seller"] == "Seller"
    assert event["buyer"] == "Buyer"
    assert event["seller_earnings"] == 950


@pytest.mark.asyncio
async def test_market_purchase_stays_successful_when_sale_broadcast_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PubSub é best-effort e não pode desfazer semanticamente um commit Lua."""
    listing_id = "123e4567-e89b-12d3-a456-426614174000"
    listing = {
        "listing_id": listing_id,
        "seller": "Seller",
        "powerup_id": "scanner",
        "price": 1000,
    }
    redis_client = AsyncMock()
    redis_client.zrange.return_value = [(json.dumps(listing), 1000.0)]
    redis_client.eval.return_value = "ok"
    redis_client.publish.side_effect = RuntimeError("pubsub indisponível")
    monkeypatch.setattr(main_module, "redis_client", redis_client)

    result = await main_module.buy_from_market(
        "regtest",
        main_module.MarketBuyRequest(username="Buyer", listing_id=listing_id),
    )

    assert result["status"] == "purchased"
    assert result["buyer"] == "Buyer"
    assert result["seller"] == "Seller"


@pytest.mark.asyncio
async def test_skill_upgrade_checks_and_mutates_in_one_redis_script(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ponto disponível e nível máximo não podem sofrer race TOCTOU."""
    redis_client = MagicMock()
    redis_client.eval = AsyncMock(return_value=["ok", 1, 0])
    redis_client.hgetall = AsyncMock(
        return_value={"points_remaining": "1", "mining_level": "0"}
    )
    redis_client.hget = AsyncMock(return_value="10")
    pipe = MagicMock()
    pipe.hincrby.return_value = pipe
    pipe.expire.return_value = pipe
    pipe.execute = AsyncMock(return_value=[1, 0, True])
    redis_client.pipeline.return_value = pipe
    monkeypatch.setattr(main_module, "redis_client", redis_client)
    monkeypatch.setattr(
        main_module,
        "get_skills",
        AsyncMock(return_value={"branches": {}, "points_remaining": 0}),
    )

    result = await main_module.upgrade_skill(
        "regtest",
        "Miner",
        main_module.SkillUpgradeRequest(username="Miner", branch="mining"),
    )

    assert result["points_remaining"] == 0
    redis_client.eval.assert_awaited_once()
    redis_client.pipeline.assert_not_called()
    redis_client.hgetall.assert_not_awaited()


def test_stats_update_accepts_fields_used_by_daily_missions() -> None:
    """Campos consumidos pelo motor de missões devem pertencer ao contrato."""
    payload = main_module.StatsUpdate(
        username="Miner",
        rbf_used=1,
        max_round_earnings=50000,
    )

    assert payload.rbf_used == 1
    assert payload.max_round_earnings == 50000


# ---------------------------------------------------------------------------
# Fase 5.5: rollover de temporada (prazo de claim + reset)
# ---------------------------------------------------------------------------


def _hset_fields(call) -> dict | None:
    """Extrai os campos gravados por um hset (mapping= ou args posicionais)."""
    if "mapping" in call.kwargs:
        return call.kwargs["mapping"]
    if len(call.args) >= 3:
        return {call.args[1]: call.args[2]}
    return None


@pytest.mark.asyncio
async def test_season_rollover_same_season_is_noop() -> None:
    """Mesmo season_id → não reseta, apenas grava o season_id atual."""
    redis_client = AsyncMock()
    current = season_pass._get_current_season_id()
    redis_client.hgetall.return_value = {"season_id": current, "level": "5", "xp": "30"}

    result = await season_pass.ensure_season_rollover(
        "signet", "Miner", _key, redis_client, _definition
    )

    assert result["is_new_season"] is False
    assert result["season_ended"] is False
    # Não reseta: nenhum hset grava level/xp/premium/claimed.
    fields = [f for f in (_hset_fields(c) for c in redis_client.hset.await_args_list) if f]
    assert not any("level" in f for f in fields)
    # O season_id atual é gravado (args posicionais).
    assert any("season_id" in f for f in fields)


@pytest.mark.asyncio
async def test_season_rollover_expired_claim_period_resets() -> None:
    """Temporada antiga com prazo de claim expirado → reseta nível/XP/premium/claimed."""
    redis_client = AsyncMock()
    # season_2025_q1 termina em 2025-04-01 — prazo de claim (7 dias) expirou.
    redis_client.hgetall.return_value = {
        "season_id": "season_2025_q1",
        "level": "20",
        "xp": "50",
        "premium": "1",
        "claimed_rewards": "[1, 2]",
    }

    result = await season_pass.ensure_season_rollover(
        "signet", "Miner", _key, redis_client, _definition
    )

    assert result["is_new_season"] is True
    assert result["season_ended"] is False  # prazo expirou → reset, não claim
    # O reset grava level/xp/premium/claimed = 0/[]
    fields = [f for f in (_hset_fields(c) for c in redis_client.hset.await_args_list) if f]
    reset_mapping = next((f for f in fields if "level" in f), None)
    assert reset_mapping is not None
    assert reset_mapping["level"] == "0"
    assert reset_mapping["xp"] == "0"
    assert reset_mapping["premium"] == "0"
    assert reset_mapping["claimed_rewards"] == "[]"


@pytest.mark.asyncio
async def test_season_rollover_active_claim_period_keeps_data() -> None:
    """Temporada antiga dentro do prazo de claim → mantém dados (season_ended)."""
    redis_client = AsyncMock()
    redis_client.hgetall.return_value = {
        "season_id": "season_2026_q3",
        "level": "15",
        "xp": "10",
    }
    from unittest.mock import patch as sync_patch
    from datetime import datetime as real_datetime, UTC as real_UTC, timedelta as real_timedelta

    # Força: temporada atual = q4; fim da q3 = ontem (dentro do prazo de 7 dias).
    now = real_datetime.now(real_UTC)
    with sync_patch.object(
        season_pass, "_get_current_season_id", return_value="season_2026_q4"
    ), sync_patch.object(
        season_pass,
        "_get_season_end_for_season_id",
        return_value=now - real_timedelta(days=1),
    ):
        result = await season_pass.ensure_season_rollover(
            "signet", "Miner", _key, redis_client, _definition
        )

    assert result["is_new_season"] is True
    assert result["season_ended"] is True
    assert result["claim_period_active"] is True
    assert result["claim_deadline"] != ""
    # Não reseta: nenhum hset grava level/xp
    fields = [f for f in (_hset_fields(c) for c in redis_client.hset.await_args_list) if f]
    assert not any("level" in f for f in fields)


@pytest.mark.asyncio
async def test_add_season_xp_blocked_when_season_ended() -> None:
    """XP não é somado em temporada encerrada (prazo de claim ativo)."""
    redis_client = AsyncMock()
    redis_client.hgetall.return_value = {
        "season_id": "season_2026_q3",
        "level": "15",
        "xp": "10",
    }
    from unittest.mock import patch as sync_patch
    from datetime import datetime as real_datetime, UTC as real_UTC, timedelta as real_timedelta

    now = real_datetime.now(real_UTC)
    with sync_patch.object(
        season_pass, "_get_current_season_id", return_value="season_2026_q4"
    ), sync_patch.object(
        season_pass,
        "_get_season_end_for_season_id",
        return_value=now - real_timedelta(days=1),
    ):
        result = await season_pass.add_season_xp(
            "signet", "Miner", 50, _key, _key, _key, redis_client, _definition
        )

    assert result["xp_added"] == 0
    assert result["season_ended"] is True
    # Não soma XP: nenhum hset grava xp
    fields = [f for f in (_hset_fields(c) for c in redis_client.hset.await_args_list) if f]
    assert not any("xp" in f for f in fields)


# ---------------------------------------------------------------------------
# Fase 5 (auditoria): migração de saldo condicional + premium em temporada
# encerrada
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_player_state_migrates_balance_only_when_field_is_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fase G: o sync migra saldo local apenas antes de o campo existir.

    O valor zero pode ser resultado legítimo de uma compra; tratá-lo como
    "não inicializado" ressuscitaria um saldo local stale.
    """
    redis_client = AsyncMock()
    monkeypatch.setattr(main_module, "redis_client", redis_client)
    monkeypatch.setattr(main_module, "get_network_definition", lambda r: _definition(r))
    monkeypatch.setattr(main_module, "player_state_key", lambda r, u: f"test:{r}:{u}")
    monkeypatch.setattr(main_module, "matching_username", lambda a, b: "Miner")
    monkeypatch.setattr(main_module, "get_player_state", AsyncMock(return_value={}))

    # Caso 1: campo ausente → migração inicial permitida uma única vez.
    redis_client.hget.return_value = None
    await main_module.update_player_state(
        "regtest", "Miner", main_module.PlayerStateUpdate(username="Miner", balance=500)
    )
    hset_mapping = redis_client.hset.await_args.kwargs.get("mapping")
    assert hset_mapping is not None
    assert hset_mapping.get("balance") == "500"

    # Caso 2: armazenado = 0 → NÃO ressuscita saldo local stale.
    redis_client.hget.return_value = "0"
    redis_client.hset.reset_mock()
    await main_module.update_player_state(
        "regtest", "Miner", main_module.PlayerStateUpdate(username="Miner", balance=500)
    )
    redis_client.hset.assert_not_awaited()

    # Caso 3: armazenado > 0 → também preserva a fonte de verdade.
    redis_client.hget.return_value = "1000"
    redis_client.hset.reset_mock()
    await main_module.update_player_state(
        "regtest", "Miner", main_module.PlayerStateUpdate(username="Miner", balance=500)
    )
    redis_client.hset.assert_not_awaited()


@pytest.mark.asyncio
async def test_buy_season_premium_blocked_when_season_ended() -> None:
    """Fase 5.5: premium não pode ser comprado em temporada encerrada."""
    redis_client = AsyncMock()
    redis_client.hgetall.return_value = {
        "season_id": "season_2026_q3",
        "level": "15",
        "xp": "10",
    }
    from unittest.mock import patch as sync_patch
    from datetime import datetime as real_datetime, UTC as real_UTC, timedelta as real_timedelta

    now = real_datetime.now(real_UTC)
    with sync_patch.object(
        season_pass, "_get_current_season_id", return_value="season_2026_q4"
    ), sync_patch.object(
        season_pass,
        "_get_season_end_for_season_id",
        return_value=now - real_timedelta(days=1),
    ):
        with pytest.raises(ValueError, match="Temporada encerrada"):
            await season_pass.buy_season_premium(
                "signet", "Miner", _key, _key, _key, redis_client, _definition
            )
    # O débito atômico (eval) NÃO é chamado — a compra é bloqueada antes.
    redis_client.eval.assert_not_awaited()



