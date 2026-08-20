# ==========================================================================
# Fase 10: Season Pass — Passaporte de Temporada
# ==========================================================================

import json
from datetime import UTC, datetime
from typing import Any

# Configurações da temporada
SEASON_DURATION_DAYS = 28  # 4 semanas
SEASON_FREE_LEVELS = 20
SEASON_PREMIUM_LEVELS = 20  # 21-40
SEASON_XP_PER_LEVEL = 100
SEASON_PREMIUM_UNLOCK_DAYS = 7  # 7 dias grátis após completar

# Definição de recompensas por nível
SEASON_FREE_REWARDS = {
    1: {"type": "sats", "value": 500},
    2: {"type": "sats", "value": 1000},
    3: {"type": "hint", "value": 1},
    4: {"type": "sats", "value": 1500},
    5: {"type": "sats", "value": 2000},
    6: {"type": "powerup", "value": "scanner"},
    7: {"type": "sats", "value": 2500},
    8: {"type": "sats", "value": 3000},
    9: {"type": "hint", "value": 2},
    10: {"type": "sats", "value": 5000},
    11: {"type": "sats", "value": 5000},
    12: {"type": "powerup", "value": "time_freeze"},
    13: {"type": "sats", "value": 7500},
    14: {"type": "sats", "value": 10000},
    15: {"type": "hint", "value": 3},
    16: {"type": "sats", "value": 12500},
    17: {"type": "sats", "value": 15000},
    18: {"type": "powerup", "value": "magnet"},
    19: {"type": "sats", "value": 20000},
    20: {"type": "sats", "value": 25000, "bonus": "season_badge"},
}

SEASON_PREMIUM_REWARDS = {
    21: {"type": "sats", "value": 30000},
    22: {"type": "card", "value": "rare"},
    23: {"type": "sats", "value": 35000},
    24: {"type": "powerup", "value": "precision"},
    25: {"type": "sats", "value": 50000},
    26: {"type": "card", "value": "epic"},
    27: {"type": "sats", "value": 60000},
    28: {"type": "powerup", "value": "double_combo"},
    29: {"type": "sats", "value": 75000},
    30: {"type": "card", "value": "legendary"},
    31: {"type": "sats", "value": 100000},
    32: {"type": "bonus", "value": "reward_plus_5pct", "duration_days": 7},
    33: {"type": "sats", "value": 125000},
    34: {"type": "card", "value": "epic"},
    35: {"type": "sats", "value": 150000},
    36: {"type": "powerup", "value": "scanner"},
    37: {"type": "sats", "value": 200000},
    38: {"type": "card", "value": "rare"},
    39: {"type": "sats", "value": 250000},
    40: {"type": "bonus", "value": "reward_plus_10pct", "duration_days": 14},
}


def _get_current_season_id() -> str:
    """Retorna o ID da temporada atual baseado na data."""
    now = datetime.now(UTC)
    quarter = (now.month - 1) // 3
    year = now.year
    return f"season_{year}_q{quarter + 1}"


def _get_season_end_date() -> str:
    """Retorna a data de fim da temporada atual."""
    now = datetime.now(UTC)
    month = now.month
    year = now.year
    if month <= 3:
        end = datetime(year, 4, 1, tzinfo=UTC)
    elif month <= 6:
        end = datetime(year, 7, 1, tzinfo=UTC)
    elif month <= 9:
        end = datetime(year, 10, 1, tzinfo=UTC)
    else:
        end = datetime(year + 1, 1, 1, tzinfo=UTC)
    return end.isoformat()


def _get_season_start_date() -> str:
    """Retorna a data de início da temporada atual."""
    now = datetime.now(UTC)
    month = now.month
    year = now.year
    if month <= 3:
        start = datetime(year, 1, 1, tzinfo=UTC)
    elif month <= 6:
        start = datetime(year, 4, 1, tzinfo=UTC)
    elif month <= 9:
        start = datetime(year, 7, 1, tzinfo=UTC)
    else:
        start = datetime(year, 10, 1, tzinfo=UTC)
    return start.isoformat()


async def get_season_data(
    realm_id: str,
    username: str,
    season_key_fn,
    player_state_key_fn,
    powerups_key_fn,
    redis_client,
    get_network_definition_fn,
) -> dict[str, Any]:
    """Retorna dados da temporada atual do jogador."""
    definition = get_network_definition_fn(realm_id)
    season_id = _get_current_season_id()
    sk_key = season_key_fn(definition.realm_id, username)

    raw = await redis_client.hgetall(sk_key)
    current_level = int(raw.get("level", 0))
    current_xp = int(raw.get("xp", 0))
    is_premium = raw.get("premium", "0") == "1"
    claimed_rewards = (
        json.loads(raw.get("claimed_rewards", "[]"))
        if raw.get("claimed_rewards")
        else []
    )

    xp_for_next = SEASON_XP_PER_LEVEL
    xp_remaining = xp_for_next - current_xp
    free_rewards = {}
    premium_rewards = {}

    for lvl in range(1, SEASON_FREE_LEVELS + 1):
        if lvl in SEASON_FREE_REWARDS:
            free_rewards[lvl] = {
                **SEASON_FREE_REWARDS[lvl],
                "unlocked": current_level >= lvl,
                "claimed": lvl in claimed_rewards,
            }

    for lvl in range(
        SEASON_FREE_LEVELS + 1,
        SEASON_FREE_LEVELS + SEASON_PREMIUM_LEVELS + 1,
    ):
        if lvl in SEASON_PREMIUM_REWARDS:
            premium_rewards[lvl] = {
                **SEASON_PREMIUM_REWARDS[lvl],
                "unlocked": is_premium and current_level >= lvl,
                "claimed": lvl in claimed_rewards,
            }

    season_end = _get_season_end_date()
    end_time = datetime.fromisoformat(season_end)
    now = datetime.now(UTC)
    remaining_seconds = max(0, int((end_time - now).total_seconds()))

    return {
        "season_id": season_id,
        "level": current_level,
        "xp": current_xp,
        "xp_for_next": xp_for_next,
        "xp_remaining": max(0, xp_remaining),
        "is_premium": is_premium,
        "free_rewards": free_rewards,
        "premium_rewards": premium_rewards,
        "season_end": season_end,
        "season_end_seconds": remaining_seconds,
        "claimed_rewards": claimed_rewards,
    }


async def add_season_xp(
    realm_id: str,
    username: str,
    xp_amount: int,
    season_key_fn,
    player_state_key_fn,
    powerups_key_fn,
    redis_client,
    get_network_definition_fn,
) -> dict[str, Any]:
    """Adiciona XP à temporada do jogador."""
    if xp_amount <= 0:
        raise ValueError("XP deve ser positivo")

    definition = get_network_definition_fn(realm_id)
    sk_key = season_key_fn(definition.realm_id, username)
    raw = await redis_client.hgetall(sk_key)
    current_level = int(raw.get("level", 0))
    current_xp = int(raw.get("xp", 0))

    new_xp = current_xp + xp_amount
    new_level = current_level
    while (
        new_xp >= SEASON_XP_PER_LEVEL
        and new_level < SEASON_FREE_LEVELS + SEASON_PREMIUM_LEVELS
    ):
        new_xp -= SEASON_XP_PER_LEVEL
        new_level += 1

    await redis_client.hset(
        sk_key,
        mapping={"level": str(new_level), "xp": str(new_xp)},
    )
    await redis_client.expire(sk_key, 86400 * 30)

    return {
        "level": new_level,
        "xp": new_xp,
        "xp_added": xp_amount,
        "leveled_up": new_level > current_level,
    }


async def claim_season_reward(
    realm_id: str,
    username: str,
    reward_level: int,
    season_key_fn,
    player_state_key_fn,
    powerups_key_fn,
    redis_client,
    get_network_definition_fn,
) -> dict[str, Any]:
    """Reclama uma recompensa com validação e crédito atômicos no Redis."""
    definition = get_network_definition_fn(realm_id)
    if reward_level in SEASON_FREE_REWARDS:
        reward = SEASON_FREE_REWARDS[reward_level]
    elif reward_level in SEASON_PREMIUM_REWARDS:
        reward = SEASON_PREMIUM_REWARDS[reward_level]
    else:
        raise ValueError("Recompensa não encontrada")

    sk_key = season_key_fn(definition.realm_id, username)
    ps_key = player_state_key_fn(definition.realm_id, username)
    pu_key = powerups_key_fn(definition.realm_id, username)
    premium_required = "1" if reward_level > SEASON_FREE_LEVELS else "0"

    lua_script = """
    local season_key = KEYS[1]
    local player_key = KEYS[2]
    local powerups_key = KEYS[3]
    local reward_level = tonumber(ARGV[1])
    local premium_required = ARGV[2] == '1'
    local reward_type = ARGV[3]
    local reward_value = ARGV[4]

    local current_level = tonumber(redis.call('hget', season_key, 'level') or '0')
    if current_level < reward_level then
        return 'level_locked'
    end
    if premium_required and redis.call('hget', season_key, 'premium') ~= '1' then
        return 'premium_locked'
    end

    local claimed_json = redis.call('hget', season_key, 'claimed_rewards') or '[]'
    local decoded_ok, claimed = pcall(cjson.decode, claimed_json)
    if not decoded_ok or type(claimed) ~= 'table' then
        claimed = {}
    end
    for _, claimed_level in ipairs(claimed) do
        if tonumber(claimed_level) == reward_level then
            return 'already_claimed'
        end
    end

    if reward_type == 'sats' then
        redis.call('hincrby', player_key, 'balance', tonumber(reward_value))
    elseif reward_type == 'hint' then
        redis.call('hincrby', player_key, 'hints', tonumber(reward_value))
    elseif reward_type == 'powerup' then
        redis.call('hincrby', powerups_key, reward_value, 1)
    end

    table.insert(claimed, reward_level)
    redis.call('hset', season_key, 'claimed_rewards', cjson.encode(claimed))
    redis.call('expire', season_key, 2592000)
    return 'ok'
    """
    result = await redis_client.eval(
        lua_script,
        3,
        sk_key,
        ps_key,
        pu_key,
        str(reward_level),
        premium_required,
        reward["type"],
        str(reward["value"]),
    )
    status = result.decode() if isinstance(result, bytes) else str(result)
    if status == "already_claimed":
        raise ValueError("Recompensa já reclamada")
    if status == "level_locked":
        raise ValueError("Nível não desbloqueado")
    if status == "premium_locked":
        raise ValueError("Nível premium não desbloqueado")
    if status != "ok":
        raise RuntimeError(f"Resultado inesperado ao reclamar recompensa: {status}")

    return {"reward": reward, "claimed_level": reward_level}


async def buy_season_premium(
    realm_id: str,
    username: str,
    season_key_fn,
    player_state_key_fn,
    powerups_key_fn,
    redis_client,
    get_network_definition_fn,
) -> dict[str, Any]:
    """Compra acesso premium com débito e ativação atômicos no Redis."""
    definition = get_network_definition_fn(realm_id)
    ps_key = player_state_key_fn(definition.realm_id, username)
    sk_key = season_key_fn(definition.realm_id, username)
    premium_cost = 50000

    lua_script = """
    local player_key = KEYS[1]
    local season_key = KEYS[2]
    local premium_cost = tonumber(ARGV[1])

    if redis.call('hget', season_key, 'premium') == '1' then
        return 'already_premium'
    end

    local balance = tonumber(redis.call('hget', player_key, 'balance') or '0')
    if balance < premium_cost then
        return 'insufficient_balance'
    end

    redis.call('hincrby', player_key, 'balance', -premium_cost)
    redis.call('hset', season_key, 'premium', '1')
    redis.call('expire', season_key, 2592000)
    return 'ok'
    """
    result = await redis_client.eval(
        lua_script,
        2,
        ps_key,
        sk_key,
        str(premium_cost),
    )
    status = result.decode() if isinstance(result, bytes) else str(result)
    if status == "insufficient_balance":
        raise ValueError("Saldo insuficiente")
    if status == "already_premium":
        raise ValueError("Passe premium já adquirido")
    if status != "ok":
        raise RuntimeError(f"Resultado inesperado ao comprar passe premium: {status}")

    return {"is_premium": True, "cost": premium_cost}
