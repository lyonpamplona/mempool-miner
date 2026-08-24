"""Chaves Redis isoladas por realm e migração dos nomes legados."""

from __future__ import annotations

import redis.asyncio as redis

from app.config import validate_realm_id

PREFIX = "mempool_miner:v2"
LEGACY_LEADERBOARD_KEY = "global_leaderboard"
LEGACY_MEMPOOL_COUNT_KEY = "mempool_count"
MIGRATE_LEADERBOARD_SCRIPT = """
if redis.call('exists', KEYS[1]) == 1 then
  return 0
end
local entries = redis.call('zrange', KEYS[2], 0, -1, 'WITHSCORES')
for index = 1, #entries, 2 do
  redis.call('zadd', KEYS[1], entries[index + 1], entries[index])
end
return #entries / 2
"""
MIGRATE_COUNTER_SCRIPT = """
if redis.call('exists', KEYS[1]) == 1 then
  return 0
end
local legacy = redis.call('get', KEYS[2])
if legacy then
  redis.call('set', KEYS[1], legacy)
  return 1
end
return 0
"""

ENERGY_SPEND_SCRIPT = """
local round_state = redis.call('get', KEYS[2])
local energy_max = tonumber(redis.call('hget', KEYS[1], 'max') or ARGV[2])
local current = tonumber(redis.call('hget', KEYS[1], 'current') or energy_max)
if round_state == 'spent' then
  return {0, current}
end
if round_state == 'refunded' then
  return {-2, current}
end

local now = tonumber(ARGV[1])
local last_refill = tonumber(redis.call('hget', KEYS[1], 'last_refill') or now)
local refill_interval = tonumber(ARGV[3])
local refills = math.floor((now - last_refill) / refill_interval)
if refills > 0 then
  current = math.min(current + refills, energy_max)
  last_refill = last_refill + (refills * refill_interval)
end
if current <= 0 then
  return {-1, current}
end

current = current - 1
redis.call('hset', KEYS[1],
  'current', tostring(current),
  'last_refill', tostring(last_refill),
  'max', tostring(energy_max))
redis.call('expire', KEYS[1], tonumber(ARGV[5]))
redis.call('set', KEYS[2], 'spent', 'EX', tonumber(ARGV[4]))
return {1, current}
"""

ENERGY_REFUND_SCRIPT = """
local round_state = redis.call('get', KEYS[2])
local energy_max = tonumber(redis.call('hget', KEYS[1], 'max') or ARGV[1])
local current = tonumber(redis.call('hget', KEYS[1], 'current') or energy_max)
if round_state == 'refunded' then
  return {0, current}
end
if round_state ~= 'spent' then
  return {-1, current}
end

current = math.min(current + 1, energy_max)
redis.call('hset', KEYS[1], 'current', tostring(current), 'max', tostring(energy_max))
redis.call('expire', KEYS[1], tonumber(ARGV[3]))
redis.call('set', KEYS[2], 'refunded', 'EX', tonumber(ARGV[2]))
return {1, current}
"""


ENERGY_BUY_SCRIPT = """
local state_key = KEYS[1]
local energy_key = KEYS[2]
local cost = tonumber(ARGV[1])
local amount = tonumber(ARGV[2])
local default_max = tonumber(ARGV[3])
local refill_interval = tonumber(ARGV[4])
local now = tonumber(ARGV[5])
local energy_ttl = tonumber(ARGV[6])

local state_type = redis.call('type', state_key)['ok']
local energy_type = redis.call('type', energy_key)['ok']
if (state_type ~= 'none' and state_type ~= 'hash')
    or (energy_type ~= 'none' and energy_type ~= 'hash') then
    return {-3, 0, 0}
end

local balance = tonumber(redis.call('hget', state_key, 'balance') or '0')
if balance < cost then
    return {-1, 0, balance}
end

local current = tonumber(redis.call('hget', energy_key, 'current') or '0')
local energy_max = tonumber(redis.call('hget', energy_key, 'max') or default_max)
local last_refill = tonumber(redis.call('hget', energy_key, 'last_refill') or now)
local refills = math.floor((now - last_refill) / refill_interval)
if refills > 0 then
    current = math.min(current + refills, energy_max)
    last_refill = last_refill + (refills * refill_interval)
end
if current >= energy_max then
    return {-2, current, balance}
end

local new_current = math.min(current + amount, energy_max)
local new_balance = redis.call('hincrby', state_key, 'balance', -cost)
redis.call('hset', energy_key,
    'current', tostring(new_current),
    'last_refill', tostring(last_refill),
    'max', tostring(energy_max))
redis.call('expire', energy_key, energy_ttl)
return {1, new_current, new_balance}
"""


def events_channel(realm_id: str) -> str:
    """Canal ao vivo de um realm."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:events"


def mempool_count_key(realm_id: str) -> str:
    """Contador observado de um realm."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:mempool_count"


def leaderboard_key(realm_id: str) -> str:
    """Leaderboard independente de um realm."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:leaderboard"


def epoch_key(realm_id: str) -> str:
    """Epoch atual usada para invalidar backlog após um bloco."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:epoch"


def realm_state_key(realm_id: str) -> str:
    """Snapshot operacional mais recente; a API expõe somente campos permitidos."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:state"


def dedupe_key(realm_id: str, epoch: str) -> str:
    """Conjunto temporário de TXIDs já publicados na epoch."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:seen:{epoch}"


def node_status_key(node_id: str) -> str:
    """Heartbeat operacional de uma origem fisica."""
    return f"{PREFIX}:node:{validate_realm_id(node_id)}:status"


def ingestor_lease_key(realm_id: str) -> str:
    """Lease que impede dois ingestores de publicar no mesmo realm."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:ingestor_lease"


# Fase 4: Leaderboard Epochs — reset a cada 2016 blocos
def epoch_block_counter_key(realm_id: str) -> str:
    """Contador de blocos para reset do leaderboard (epoch de 2016 blocos)."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:block_counter"


def epoch_id_key(realm_id: str) -> str:
    """ID da epoch atual do leaderboard (incrementa a cada 2016 blocos)."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:epoch_id"


# Fase 5: Mining Pools — guildas por prefixo
def pool_leaderboard_key(realm_id: str) -> str:
    """Leaderboard de pools (guildas) por realm."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:pools"


# Fase 3: Estado do jogador — persistencia no Redis
def player_state_key(realm_id: str, username: str) -> str:
    """Estado persistente do jogador (saldo, hardware, lightning, combo, etc.)."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:player:{username}"


# Fase 7: Achievements — tracking de stats e conquistas
def achievements_key(realm_id: str, username: str) -> str:
    """Hash Redis com achievements desbloqueados do jogador."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:achievements:{username}"


def player_stats_key(realm_id: str, username: str) -> str:
    """Hash Redis com contadores de stats para calculo de progresso."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:stats:{username}"


# Fase 7: Streaks (Login Diário) — tracking de login consecutivo
def streak_key(realm_id: str, username: str) -> str:
    """Streak do jogador: lastLogin, streakCount, totalLogins."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:streak:{username}"


# Fase 7: Daily Rewards — recompensa semanal de 7 dias
def daily_reward_key(realm_id: str, username: str) -> str:
    """Daily reward do jogador: currentDay, lastClaimDate."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:daily_reward:{username}"


# Fase 8: Level & Rank — tracking de nível e XP do jogador
def level_key(realm_id: str, username: str) -> str:
    """Hash Redis com nível, XP e rank do jogador."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:level:{username}"


# Fase 8: Missões Diárias & Semanais — tracking de progresso
def missions_key(realm_id: str, username: str, date: str) -> str:
    """Hash Redis com progresso das missões do jogador para uma data específica."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:missions:{username}:{date}"


def weekly_missions_key(realm_id: str, username: str, week: str) -> str:
    """Hash Redis com progresso da missão semanal do jogador para uma semana específica."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:missions_weekly:{username}:{week}"


def powerups_key(realm_id: str, username: str) -> str:
    """Hash Redis com inventário de power-ups do jogador."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:powerups:{username}"


# Fase 3: Chat em Tempo Real
def chat_messages_key(realm_id: str) -> str:
    """Lista Redis com mensagens recentes do chat do realm."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:chat:messages"


def chat_rate_key(realm_id: str, username: str) -> str:
    """Contador de rate limiting para chat do jogador."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:chat:rate:{username}"


# Fase 3: Tokens Colecionáveis (Block Cards)
def cards_set_key(realm_id: str, username: str) -> str:
    """Set Redis com IDs dos block cards do jogador."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:cards:{username}"


def card_detail_key(realm_id: str, owner: str, card_id: str) -> str:
    """Hash Redis com detalhes de um block card específico."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:card:{owner}:{card_id}"


# Fase 3: Mercado de Power-ups
def market_list_key(realm_id: str) -> str:
    """Sorted Set Redis com power-ups à venda no mercado do realm."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:market:list"


def market_history_key(realm_id: str) -> str:
    """Lista Redis com histórico de transações do mercado do realm."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:market:history"


def market_price_index_key(realm_id: str, powerup_id: str) -> str:
    """Lista Redis com histórico de preços de um power-up específico."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:market:price:{powerup_id}"


# Fase 9: Desafios PvP — tracking de desafios head-to-head
def pvp_match_key(realm_id: str, challenger: str, challenged: str) -> str:
    """Hash Redis com estado de um desafio PvP entre dois jogadores.
    
    A chave é normalizada para que o challenger (alfabeticamente primeiro)
    sempre venha primeiro, garantindo unicidade.
    """
    sorted_names = sorted([challenger, challenged])
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:pvp:{sorted_names[0]}:{sorted_names[1]}"


def pvp_active_channel(realm_id: str) -> str:
    """Canal PubSub para eventos PvP ao vivo de um realm."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:pvp_events"


# Fase 10: Skill Tree — tracking de habilidades do jogador
def skills_key(realm_id: str, username: str) -> str:
    """Hash Redis com árvore de habilidades do jogador.

    Fields: mining_level, search_level, lightning_level, points_remaining.
    """
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:skills:{username}"


# Fase 10: Staking de Sats — tracking de stakes ativos e histórico
def staking_key(realm_id: str, username: str) -> str:
    """Hash Redis com stake ativo do jogador: amount, duration, start_time, end_time, bonus_percent."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:staking:{username}"


def staking_history_key(realm_id: str, username: str) -> str:
    """Lista Redis com histórico de stakes do jogador."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:staking_history:{username}"


# Fase 10: Mempool Crates — tracking de loot boxes
def crates_key(realm_id: str, username: str) -> str:
    """Hash Redis com estado de crates do jogador.

    Fields:
        free_crates: crates gratuitas disponíveis (acumulam a cada 10 blocos)
        owned_crates: crates compradas/disponíveis para abrir
        last_free_block: último bloco onde o jogador recebeu crate grátis
        legendary_bonus: bônus permanente acumulado (+5% por item legendário)
        inventory: JSON array de itens já recebidos (histórico)
    """
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:crates:{username}"


# Fase 10: Season Pass — tracking de temporada do jogador
def season_key(realm_id: str, username: str) -> str:
    """Hash Redis com dados da temporada do jogador (season_id, level, xp, premium, claimed_rewards)."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:season:{username}"


# Fase Sprint: Leaderboard separado para o modo sprint
def sprint_leaderboard_key(realm_id: str) -> str:
    """Leaderboard independente do modo sprint por realm."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:sprint_leaderboard"


# Fase 11: Sistema de Amigos & Co-op — tracking de amigos e status online
def friends_key(realm_id: str, username: str) -> str:
    """Chave Redis para lista de amigos do jogador."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:friends:{username}"


def online_key(realm_id: str) -> str:
    """Hash Redis com jogadores online no realm: {username: timestamp}."""
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:online"


# Fase 11: Energy System — tracking de energia do jogador
def energy_key(realm_id: str, username: str) -> str:
    """Hash Redis com estado de energia do jogador.

    Fields:
        current: energia atual (0-10)
        last_refill: timestamp UNIX da última regeneração
        max: energia máxima (10)
    """
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:energy:{username}"


def energy_round_key(realm_id: str, username: str, round_id: str) -> str:
    """Estado idempotente do débito/estorno de energia de uma rodada."""
    return (
        f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:"
        f"energy_round:{username}:{round_id}"
    )


# Fase: Mini-game Decoder — tracking de partidas e streaks
def decoder_key(realm_id: str, username: str) -> str:
    """Hash Redis com estado do mini-game Decoder do jogador.

    Fields:
        last_play: timestamp da última partida (para cooldown)
        streak: sequência de acertos consecutivos
        wins: total de vitórias
    """
    return f"{PREFIX}:{{{validate_realm_id(realm_id)}}}:decoder:{username}"


async def migrate_legacy_default(client: redis.Redis, default_realm: str) -> None:
    """Copia dados legados para o realm padrao sem remover a origem de rollback.

    Executa dois scripts Lua idempotentes:
    1. Migra o leaderboard legacy (``global_leaderboard``) para o realm padrao.
    2. Migra o contador legacy (``mempool_count``) para o realm padrao.

    Se o destino ja existe, o script retorna 0 sem alterar nada.

    Args:
        client: Cliente Redis async.
        default_realm: Realm padrao (ex: ``regtest``).
    """
    await client.eval(
        MIGRATE_LEADERBOARD_SCRIPT,
        2,
        leaderboard_key(default_realm),
        LEGACY_LEADERBOARD_KEY,
    )
    await client.eval(
        MIGRATE_COUNTER_SCRIPT,
        2,
        mempool_count_key(default_realm),
        LEGACY_MEMPOOL_COUNT_KEY,
    )
