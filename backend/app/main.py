"""API multi-rede do Mempool Miner.

Os ingestors singleton publicam eventos namespaced no Redis; este processo não
abre ZMQ nem consulta RPC e, por isso, pode ser escalado sem duplicar eventos.
"""

from __future__ import annotations

import asyncio
import datetime
import hashlib
import json
import logging
import os
import random
import time
from contextlib import asynccontextmanager
from typing import Annotated, Any
from urllib.parse import urlsplit

import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Request, Response, WebSocket, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from app.config import (
    NETWORK_CATALOG,
    NETWORKS_BY_REALM,
    NetworkDefinition,
    default_realm_id,
    validate_realm_id,
)
from app.events import event_envelope
from app.global_events import (
    GlobalEventScheduler,
    GlobalEventType,
    EVENT_META,
    EVENT_DURATION_SECONDS,
    EVENT_PREANNOUNCE_SECONDS,
    get_active_event,
    publish_event_status,
)
from app.storage import (
    PREFIX,
    achievements_key,
    cards_set_key,
    card_detail_key,
    chat_messages_key,
    chat_rate_key,
    crates_key,
    decoder_key,
    energy_key,
    events_channel,
    leaderboard_key,
    level_key,
    migrate_legacy_default,
    missions_key,
    node_status_key,
    player_stats_key,
    pool_leaderboard_key,
    player_state_key,
    realm_state_key,
    powerups_key,
    weekly_missions_key,
    market_list_key,
    market_history_key,
    market_price_index_key,
    pvp_match_key,
    pvp_active_channel,
    skills_key,
    staking_key,
    staking_history_key,
    season_key,
    friends_key,
    online_key,
)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Limite máximo de pontuação (INT32_MAX) — compatível com Redis Sorted Sets
# e evita overflow em clientes que usam int32 para ordenação.
MAX_SCORE = 2_147_483_647
DEFAULT_REALM_ID = default_realm_id()
TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
PUBLIC_NETWORK_STATUSES = frozenset(
    {"starting", "syncing", "ready", "unavailable", "stopped", "disabled"}
)
PUBLIC_EVENT_FIELDS = {
    "game_start": frozenset(
        {
            "status",
            "playable",
            "initial_block_download",
            "verification_progress",
            "pruned",
        }
    ),
    "network_status": frozenset(
        {
            "status",
            "playable",
            "initial_block_download",
            "verification_progress",
            "pruned",
        }
    ),
    "transaction_received": frozenset(
        {
            "word",
            "tx_stub",
            "is_golden",
            "is_high_fee",
            "vsize",
            "fee_rate_sat_vb",
            "is_mev",
            "expand_grid",
            "base_reward",
            "multiplier",
        }
    ),
    "block_mined": frozenset(
        {
            "block_hash",
            "mempool_count",
            "discarded_backlog",
            "is_halving_block",
        }
    ),
    "leaderboard_reset": frozenset({"realm_id", "epoch"}),
    # Boss Battles: evento de bloco especial a cada 50 blocos
    "boss_block": frozenset({
        "block_count",
        "boss_hp",
        "boss_grid_size",
        "boss_words",
        "boss_timer",
        "boss_reward_multiplier",
        "boss_loot",
    }),
    # Fase 8: Eventos Globais — pre-anúncio, início e fim
    "event_preannounce": frozenset({
        "event_type",
        "event_label",
        "event_icon",
        "event_description",
        "event_color",
        "event_preannounced",
        "event_started_at",
        "event_ends_at",
    }),
    "event_started": frozenset({
        "event_type",
        "event_label",
        "event_icon",
        "event_description",
        "event_color",
        "event_preannounced",
        "event_started_at",
        "event_ends_at",
    }),
    "event_ended": frozenset({
        "event_type",
        "event_label",
        "event_icon",
        "event_description",
        "event_color",
        "event_preannounced",
        "event_started_at",
        "event_ends_at",
    }),
}
PUBLIC_COMMON_EVENT_FIELDS = frozenset(
    {
        "schema_version",
        "event_id",
        "action",
        "network",
        "realm_id",
        "epoch",
    }
)


def environment_flag(name: str, *, default: bool = False) -> bool:
    """Interpreta uma flag de ambiente usando uma lista positiva restrita."""
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in TRUE_VALUES


def normalize_http_origin(value: str) -> str:
    """Normaliza uma origem HTTP(S) e recusa curingas, credenciais ou caminhos."""
    candidate = value.strip()
    try:
        parsed = urlsplit(candidate)
        port = parsed.port
    except ValueError as exc:
        raise RuntimeError("Origem CORS inválida") from exc

    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not parsed.hostname
        or "*" in parsed.hostname
        or any(character.isspace() for character in candidate)
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise RuntimeError("Origem CORS inválida")

    scheme = parsed.scheme.lower()
    hostname = parsed.hostname.lower()
    rendered_host = f"[{hostname}]" if ":" in hostname else hostname
    is_default_port = (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    suffix = "" if port is None or is_default_port else f":{port}"
    return f"{scheme}://{rendered_host}{suffix}"


def configured_cors_origins() -> tuple[str, ...]:
    """Carrega origens explícitas e falha fechado diante de valor inseguro."""
    raw_origins = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:8010,http://127.0.0.1:8010",
    )
    origins = tuple(
        dict.fromkeys(
            normalize_http_origin(item) for item in raw_origins.split(",") if item.strip()
        )
    )
    if not origins:
        raise RuntimeError("CORS_ORIGINS precisa conter ao menos uma origem HTTP(S)")
    return origins


def configured_trusted_hosts(origins: tuple[str, ...]) -> tuple[str, ...]:
    """Limita o cabeçalho Host às origens públicas e nomes internos conhecidos."""
    configured = os.getenv("TRUSTED_HOSTS")
    if configured is None:
        hosts = {"backend", "localhost", "127.0.0.1"}
        hosts.update(urlsplit(origin).hostname or "" for origin in origins)
    else:
        hosts = {item.strip().lower() for item in configured.split(",") if item.strip()}

    if not hosts or "*" in hosts:
        raise RuntimeError("TRUSTED_HOSTS precisa conter hosts explícitos")
    if any(
        not host or "://" in host or "/" in host or any(character.isspace() for character in host)
        for host in hosts
    ):
        raise RuntimeError("TRUSTED_HOSTS contém valor inválido")
    return tuple(sorted(hosts))


cors_origins = configured_cors_origins()
trusted_hosts = configured_trusted_hosts(cors_origins)
api_docs_enabled = environment_flag("ENABLE_API_DOCS")
redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
redis_client = redis.from_url(
    redis_url,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
)


def normalize_username(value: Any) -> str:
    """Remove espaços externos e rejeita caracteres inseguros no nickname."""
    if not isinstance(value, str):
        raise ValueError("o nickname deve ser texto")
    normalized = value.strip()
    safe_characters = normalized.replace("_", "").replace("-", "")
    if not safe_characters.isalnum():
        raise ValueError("use apenas letras, números, hífen e sublinhado")
    return normalized


Username = Annotated[
    str,
    Field(min_length=1, max_length=12),
    BeforeValidator(normalize_username),
]

PoolName = Annotated[
    str,
    Field(min_length=1, max_length=20),
    BeforeValidator(normalize_username),
]


def matching_username(path_username: str, body_username: str) -> str:
    """Normaliza a identidade do path e rejeita divergência com o body."""
    try:
        normalized_path = normalize_username(path_username)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not 1 <= len(normalized_path) <= 12:
        raise HTTPException(status_code=422, detail="Username inválido no path")
    if normalized_path != body_username:
        raise HTTPException(
            status_code=409,
            detail="Username do path diverge do body",
        )
    return normalized_path


class ScoreSubmit(BaseModel):
    """Representa uma atualização de pontuação enviada pelo cliente."""

    model_config = ConfigDict(extra="forbid")

    username: Username
    pool_name: PoolName | None = None
    score: int = Field(strict=True, ge=0, le=MAX_SCORE)


# Fase 3: Estado do jogador — modelos Pydantic
class PlayerState(BaseModel):
    """Estado persistente do jogador no Redis."""

    model_config = ConfigDict(extra="forbid")

    username: Username
    balance: int = Field(default=0, ge=0, le=MAX_SCORE)
    hardware_level: int = Field(default=1, ge=1, le=4)
    lightning_active: bool = Field(default=False)
    lightning_blocks_remaining: int = Field(default=0, ge=0, le=5)
    combo_multiplier: float = Field(default=1.0, ge=1.0, le=4.0)
    hints_used: int = Field(default=0, ge=0)
    rbf_used: int = Field(default=0, ge=0)
    mev_found: int = Field(default=0, ge=0)


class PlayerStateUpdate(BaseModel):
    """Atualização parcial do estado do jogador."""

    model_config = ConfigDict(extra="forbid")

    username: Username
    balance: int | None = None
    hardware_level: int | None = None
    lightning_active: bool | None = None
    lightning_blocks_remaining: int | None = None
    combo_multiplier: float | None = None
    hints_used: int | None = None
    rbf_used: int | None = None
    mev_found: int | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Valida o Redis, migra dados legados e inicia relays persistentes."""
    _global_event_schedulers: dict[str, GlobalEventScheduler] = {}
    try:
        await redis_client.ping()
        await migrate_legacy_default(redis_client, DEFAULT_REALM_ID)

        # Fase 1: Iniciar relays persistentes para todos os realms do catálogo
        for definition in NETWORK_CATALOG:
            realm_id = definition.realm_id
            relay = EventRelay(realm_id)
            await relay.start()
            _event_relays[realm_id] = relay
        logger.info("Relays persistentes iniciados para %d realms", len(NETWORK_CATALOG))

        # Fase 8: Iniciar schedulers de eventos globais para todos os realms
        for definition in NETWORK_CATALOG:
            realm_id = definition.realm_id
            scheduler = GlobalEventScheduler(
                redis_client,
                realm_id,
                min_interval_seconds=int(os.getenv("EVENT_MIN_INTERVAL", "1800")),
                max_interval_seconds=int(os.getenv("EVENT_MAX_INTERVAL", "3600")),
            )
            await scheduler.start()
            _global_event_schedulers[realm_id] = scheduler
        logger.info(
            "Schedulers de eventos globais iniciados para %d realms",
            len(NETWORK_CATALOG),
        )

        yield
    finally:
        # Encerrar schedulers de eventos globais
        for scheduler in _global_event_schedulers.values():
            try:
                await scheduler.stop()
            except Exception:
                logger.exception("Falha ao encerrar scheduler de evento global")
        _global_event_schedulers.clear()
        # Encerrar relays ao desligar
        for relay in _event_relays.values():
            try:
                await relay.stop()
            except Exception:
                logger.exception("Falha ao encerrar relay de eventos")
        _event_relays.clear()
        await redis_client.aclose()


app = FastAPI(
    title="Mempool Miner API",
    summary="Eventos Bitcoin multi-rede transformados em partidas de caça-palavras.",
    version="2.0.0",
    debug=False,
    lifespan=lifespan,
    openapi_url="/openapi.json" if api_docs_enabled else None,
    docs_url="/docs" if api_docs_enabled else None,
    redoc_url="/redoc" if api_docs_enabled else None,
)

# Host/CORS HTTP são tratados por security_headers(); WebSocket mantém uma
# validação de Origin própria para não depender de middlewares Starlette.

legacy_successors = {
    "/api/health": "/api/v1/health/live",
    "/api/leaderboard": f"/api/v1/networks/{DEFAULT_REALM_ID}/leaderboard",
}


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Valida Host/CORS no tráfego HTTP e aplica cabeçalhos defensivos."""
    request_host = (request.url.hostname or "").lower()
    if request_host not in trusted_hosts:
        response = JSONResponse(status_code=400, content={"detail": "Host inválido"})
    elif request.method == "OPTIONS" and request.headers.get("access-control-request-method"):
        response = Response(status_code=204)
    else:
        response = await call_next(request)

    origin = request.headers.get("origin")
    if origin in cors_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
        if request.method == "OPTIONS":
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            response.headers["Access-Control-Max-Age"] = "600"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.url.path not in {"/docs", "/redoc"}:
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"

    successor = legacy_successors.get(request.url.path)
    if successor:
        response.headers["Deprecation"] = "true"
        response.headers["Link"] = f'<{successor}>; rel="successor-version"'
    return response


@app.exception_handler(redis.RedisError)
async def redis_error_handler(request: Request, exc: redis.RedisError) -> JSONResponse:
    """Converte falhas Redis em erro público genérico sem revelar topologia.

    Retorna 503 com ``Retry-After: 5`` para indicar que o cliente deve
    tentar novamente em breve. O log interno registra o tipo da exceção.

    Args:
        request: Requisição HTTP que disparou o erro.
        exc: Exceção do Redis.

    Returns:
        JSONResponse 503 com mensagem genérica.
    """
    logger.warning(
        "Dependência de estado indisponível em %s %s (%s)",
        request.method,
        request.url.path,
        type(exc).__name__,
    )
    return JSONResponse(
        status_code=503,
        content={"detail": "Serviço temporariamente indisponível"},
        headers={"Retry-After": "5"},
    )


def get_network_definition(realm_id: str) -> NetworkDefinition:
    """Resolve somente o identificador canônico de um realm público.

    Args:
        realm_id: Identificador do realm.

    Returns:
        ``NetworkDefinition`` do catálogo.

    Raises:
        HTTPException: Se o realm não existir ou for inválido (status 404).
    """
    try:
        normalized_realm = validate_realm_id(realm_id)
    except ValueError:
        normalized_realm = ""
    if normalized_realm != realm_id:
        raise HTTPException(status_code=404, detail="Rede não encontrada")
    definition = NETWORKS_BY_REALM.get(normalized_realm)
    if definition is None:
        raise HTTPException(status_code=404, detail="Rede não encontrada")
    return definition


def websocket_origin_allowed(websocket: WebSocket) -> bool:
    """Aceita WebSocket apenas das mesmas origens explicitamente liberadas.

    Normaliza a origem (remove trailing slash, lowercase) e compara contra
    a lista ``cors_origins``. Origens ausentes ou inválidas são rejeitadas.

    Args:
        websocket: Conexão WebSocket pendente.

    Returns:
        ``True`` se a origem está na lista permitida.
    """
    origin = websocket.headers.get("origin")
    if not origin:
        return False
    try:
        normalized_origin = normalize_http_origin(origin)
    except RuntimeError:
        return False
    return normalized_origin in cors_origins


def sanitize_public_event(event: Any, expected_realm: str) -> dict[str, Any] | None:
    """Seleciona o contrato WebSocket público e torna o ID da origem opaco.

    Filtra campos permitidos por tipo de ação e substitui ``event_id`` por
    seu hash SHA-256 para evitar vazamento de identificadores internos.

    Args:
        event: Evento bruto do Redis.
        expected_realm: Realm esperado para filtragem.

    Returns:
        Dict sanitizado ou ``None`` se o evento for inválido ou de outro realm.
    """
    if not isinstance(event, dict):
        return None
    action = event.get("action")
    if not isinstance(action, str) or action not in PUBLIC_EVENT_FIELDS:
        return None
    if event.get("realm_id") != expected_realm:
        return None
    raw_event_id = event.get("event_id")
    if not isinstance(raw_event_id, str) or not raw_event_id:
        return None

    allowed_fields = PUBLIC_COMMON_EVENT_FIELDS | PUBLIC_EVENT_FIELDS[action]
    public_event = {key: event[key] for key in allowed_fields if key in event and key != "event_id"}
    public_event["event_id"] = hashlib.sha256(raw_event_id.encode("utf-8")).hexdigest()
    return public_event


def serialize_public_event(raw_event: Any, expected_realm: str) -> str | None:
    """Decodifica e serializa um evento Redis sem encaminhar campos privados."""
    if isinstance(raw_event, bytes):
        try:
            raw_event = raw_event.decode("utf-8")
        except UnicodeDecodeError:
            return None
    if not isinstance(raw_event, str):
        return None
    try:
        event = json.loads(raw_event)
    except (json.JSONDecodeError, TypeError):
        return None
    public_event = sanitize_public_event(event, expected_realm)
    if public_event is None:
        return None
    return json.dumps(public_event, separators=(",", ":"))


async def load_json(key: str) -> dict[str, Any] | None:
    """Carrega um snapshot Redis e ignora documento ausente ou corrompido."""
    raw_value = await redis_client.get(key)
    if not raw_value:
        return None
    try:
        value = json.loads(raw_value)
    except (json.JSONDecodeError, TypeError):
        logger.warning("Snapshot Redis inválido ignorado: %s", key)
        return None
    return value if isinstance(value, dict) else None


async def network_snapshot(
    realm_id: str,
    *,
    include_runtime_epoch: bool = False,
) -> dict[str, Any]:
    """Combina catálogo público com heartbeat, ocultando epoch salvo uso interno."""
    definition = get_network_definition(realm_id)
    status = await load_json(node_status_key(definition.node_id))
    state = await load_json(realm_state_key(definition.realm_id))
    observed = status or state or {}
    has_live_heartbeat = status is not None

    if not observed:
        runtime_status = "disabled" if definition.optional else "unavailable"
    elif not has_live_heartbeat and observed.get("status") != "stopped":
        runtime_status = "unavailable"
    else:
        runtime_status = str(observed.get("status", "unavailable"))
    if runtime_status not in PUBLIC_NETWORK_STATUSES:
        runtime_status = "unavailable"

    playable = (
        bool(observed.get("playable", False)) and has_live_heartbeat and runtime_status == "ready"
    )
    snapshot = {
        "realm_id": definition.realm_id,
        "network": definition.network.value,
        "display_name": definition.label,
        "status": runtime_status,
        "playable": playable,
        "initial_block_download": bool(observed.get("initial_block_download", True)),
        "verification_progress": float(observed.get("verification_progress", 0.0) or 0.0),
        "pruned": bool(observed.get("pruned", False)),
    }
    if include_runtime_epoch:
        snapshot["epoch"] = observed.get("epoch")
    return snapshot


@app.get("/api/health", tags=["Compatibilidade"], include_in_schema=False)
@app.get("/api/v1/health/live", tags=["Operação"])
async def healthcheck() -> Response:
    """Confirma que a API está viva e consegue consultar o Redis.

    ``/api/health`` é alias legado para ``/api/v1/health/live``.
    Planejado para remoção na versão 2.0.
    """
    await redis_client.ping()
    response = JSONResponse({"status": "ok"})
    response.headers["Sunset"] = '"2027-01-01"'
    return response


@app.get("/api/v1/health/ready", tags=["Operação"])
async def readiness() -> dict[str, Any]:
    """Confirma readiness sem divulgar o estado operacional dos nós.

    Diferente de ``/health/live``, este endpoint não expõe detalhes do Redis
    ou dos ingestores — apenas confirma que a API está pronta para receber
    requisições.
    """
    await redis_client.ping()
    return {"status": "ready"}


# Fase 8: Endpoint para consultar eventos globais ativos
@app.get("/api/v1/networks/{realm_id}/global-events", tags=["Eventos Globais"])
async def get_global_events(realm_id: str) -> dict[str, Any]:
    """Retorna o estado atual de eventos globais para o realm.

    Verifica se há um evento ativo, próximo (pre-anúncio) ou encerrado.

    Args:
        realm_id: Identificador do realm.

    Returns:
        Dict com ``active_event`` (se houver) e ``event_definitions``
        (metadados de todos os tipos de evento).
    """
    definition = get_network_definition(realm_id)
    active = await get_active_event(redis_client, definition.realm_id)

    # Constrói definições de todos os tipos de evento
    event_definitions = []
    for event_type in GlobalEventType:
        meta = EVENT_META[event_type]
        event_definitions.append({
            "type": event_type.value,
            "label": meta["label"],
            "icon": meta["icon"],
            "description": meta["description"],
            "color": meta["color"],
            "duration_seconds": EVENT_DURATION_SECONDS[event_type],
        })

    return {
        "realm_id": definition.realm_id,
        "active_event": active,
        "event_definitions": event_definitions,
    }


@app.get("/api/v1/networks", tags=["Redes"])
async def get_networks() -> dict[str, Any]:
    """Lista metadados públicos, sem RPC, ZMQ ou credenciais.

    Retorna o catálogo de redes conhecidas com seus snapshots sanitizados.
    O campo ``schema_version`` indica a versão do contrato da resposta.
    """
    networks = [await network_snapshot(item.realm_id) for item in NETWORK_CATALOG]
    return {
        "schema_version": 2,
        "default_realm_id": DEFAULT_REALM_ID,
        "networks": networks,
    }


@app.get("/api/v1/networks/{realm_id}/health", tags=["Redes"])
async def get_network_health(realm_id: str) -> dict[str, Any]:
    """Retorna o heartbeat sanitizado da rede selecionada.

    Args:
        realm_id: Identificador da rede.

    Returns:
        Snapshot com ``status``, ``playable``, ``initial_block_download``,
        ``verification_progress``, ``pruned`` e ``epoch``.
    """
    return await network_snapshot(realm_id)


async def submit_score_for_realm(realm_id: str, data: ScoreSubmit) -> dict[str, str | bool]:
    """Mantem atomicamente o recorde no leaderboard isolado do realm.

    Usa ``ZADD GT CH`` para atualizar apenas se a nova pontuacao for maior
    que a existente. Verifica se o realm esta ``playable`` antes de gravar.

    Fase 5: Mining Pools — se ``pool_name`` foi informado, atualiza também
    o leaderboard de pools sem alterar a identidade do jogador.

    Args:
        realm_id: Identificador do realm.
        data: Payload com ``username`` e ``score``.

    Returns:
        Dict com ``status`` e ``updated``.

    Raises:
        HTTPException: Se o realm nao estiver disponivel (status 409).
    """
    definition = get_network_definition(realm_id)
    snapshot = await network_snapshot(definition.realm_id)
    if not snapshot["playable"]:
        raise HTTPException(status_code=409, detail="Rede indisponivel para pontuacao")
    updated = await redis_client.zadd(
        leaderboard_key(definition.realm_id),
        {data.username: data.score},
        gt=True,
        ch=True,
    )

    # Fase 5: Mining Pools — guilda é metadado separado do username.
    pool_name = data.pool_name
    if pool_name:
        await redis_client.zadd(
            pool_leaderboard_key(definition.realm_id),
            {pool_name: data.score},
            gt=True,
            ch=True,
        )

    return {
        "status": "success",
        "updated": bool(updated),
        "realm_id": definition.realm_id,
    }


async def leaderboard_for_realm(realm_id: str) -> dict[str, Any]:
    """Retorna os 10 maiores recordes do realm indicado.

    Args:
        realm_id: Identificador do realm.

    Returns:
        Dict com ``realm_id`` e ``leaderboard`` (lista de dicts com ``username`` e ``score``).
    """
    definition = get_network_definition(realm_id)
    top_miners = await redis_client.zrevrange(
        leaderboard_key(definition.realm_id), 0, 9, withscores=True
    )
    leaderboard = [{"username": username, "score": int(score)} for username, score in top_miners]
    return {"realm_id": definition.realm_id, "leaderboard": leaderboard}


# Fase 5: Mining Pools — endpoint para leaderboard de pools
@app.get("/api/v1/networks/{realm_id}/pools", tags=["Leaderboard"])
async def get_pools_v1(realm_id: str) -> dict[str, Any]:
    """Lista os top 10 pools (guildas) do realm indicado.

    Args:
        realm_id: Identificador do realm.

    Returns:
        Dict com ``realm_id`` e ``pools`` (lista de dicts com ``pool_name`` e ``score``).
    """
    definition = get_network_definition(realm_id)
    top_pools = await redis_client.zrevrange(
        pool_leaderboard_key(definition.realm_id), 0, 9, withscores=True
    )
    pools = [{"pool_name": pool, "score": int(score)} for pool, score in top_pools]
    return {"realm_id": definition.realm_id, "pools": pools}


@app.post("/api/v1/networks/{realm_id}/leaderboard", tags=["Leaderboard"])
async def submit_score_v1(realm_id: str, data: ScoreSubmit) -> dict[str, str | bool]:
    """Atualiza a maior pontuação no realm indicado.

    Args:
        realm_id: Identificador do realm.
        data: Payload com ``username`` e ``score``.

    Returns:
        Dict com ``status`` e ``updated``.
    """
    return await submit_score_for_realm(realm_id, data)


@app.get("/api/v1/networks/{realm_id}/leaderboard", tags=["Leaderboard"])
async def get_leaderboard_v1(realm_id: str) -> dict[str, Any]:
    """Lista recordes do realm indicado.

    Args:
        realm_id: Identificador do realm.

    Returns:
        Dict com ``realm_id`` e ``leaderboard`` (lista de dicts com ``username`` e ``score``).
    """
    return await leaderboard_for_realm(realm_id)


@app.post("/api/leaderboard", tags=["Compatibilidade"], include_in_schema=False)
async def submit_score(data: ScoreSubmit) -> Response:
    """Alias temporário que grava somente no realm padrão.

    Planejado para remoção na versão 2.0.
    """
    result = await submit_score_for_realm(DEFAULT_REALM_ID, data)
    response = JSONResponse({"status": str(result["status"]), "updated": bool(result["updated"])})
    response.headers["Sunset"] = '"2027-01-01"'
    return response


@app.get("/api/leaderboard", tags=["Compatibilidade"], include_in_schema=False)
async def get_leaderboard() -> Response:
    """Alias temporário que lê somente o realm padrão.

    Planejado para remoção na versão 2.0.
    """
    result = await leaderboard_for_realm(DEFAULT_REALM_ID)
    response = JSONResponse({"leaderboard": result["leaderboard"]})
    response.headers["Sunset"] = '"2027-01-01"'
    return response


# Fase 3: Estado do jogador — endpoints REST
@app.get("/api/v1/networks/{realm_id}/player/{username}", tags=["Player"])
async def get_player_state(realm_id: str, username: str) -> dict[str, Any]:
    """Retorna o estado persistente do jogador.

    Args:
        realm_id: Identificador do realm.
        username: Nome do minerador.

    Returns:
        Estado do jogador ou valores padrão se não existir.
    """
    definition = get_network_definition(realm_id)
    key = player_state_key(definition.realm_id, username)
    raw = await redis_client.hgetall(key)
    if not raw:
        return {
            "username": username,
            "balance": 0,
            "hardware_level": 1,
            "lightning_active": False,
            "lightning_blocks_remaining": 0,
            "combo_multiplier": 1.0,
            "hints_used": 0,
            "rbf_used": 0,
            "mev_found": 0,
        }
    return {
        "username": username,
        "balance": int(raw.get("balance", 0)),
        "hardware_level": int(raw.get("hardware_level", 1)),
        "lightning_active": raw.get("lightning_active", "false") == "true",
        "lightning_blocks_remaining": int(raw.get("lightning_blocks_remaining", 0)),
        "combo_multiplier": float(raw.get("combo_multiplier", 1.0)),
        "hints_used": int(raw.get("hints_used", 0)),
        "rbf_used": int(raw.get("rbf_used", 0)),
        "mev_found": int(raw.get("mev_found", 0)),
    }


@app.post("/api/v1/networks/{realm_id}/player/{username}", tags=["Player"])
async def update_player_state(realm_id: str, username: str, data: PlayerStateUpdate) -> dict[str, Any]:
    """Atualiza o estado persistente do jogador.

    Args:
        realm_id: Identificador do realm.
        username: Nome do minerador.
        data: Campos a atualizar.

    Returns:
        Estado atualizado do jogador.
    """
    username = matching_username(username, data.username)
    definition = get_network_definition(realm_id)
    key = player_state_key(definition.realm_id, username)
    updates = data.model_dump(exclude={"username"}, exclude_none=True)
    if updates:
        await redis_client.hset(key, mapping=updates)
        await redis_client.expire(key, 86400)  # 24h TTL
    return await get_player_state(realm_id, username)


# Fase 7: Achievements — definicoes de conquistas
ACHIEVEMENTS: dict[str, dict[str, Any]] = {
    # Volume — palavras encontradas
    "first_word": {"name": "Primeira Palavra", "category": "volume", "icon": "⛏️", "description": "Encontre sua primeira palavra na mempool.", "requirement": {"stat": "words_found", "target": 1}, "bonus": {"type": "reward_percent", "value": 0.01}},
    "beginner_miner": {"name": "Miner Iniciante", "category": "volume", "icon": "⛏️", "description": "Encontre 10 palavras.", "requirement": {"stat": "words_found", "target": 10}, "bonus": {"type": "reward_percent", "value": 0.01}},
    "experienced_miner": {"name": "Miner Experiente", "category": "volume", "icon": "⛏️", "description": "Encontre 100 palavras.", "requirement": {"stat": "words_found", "target": 100}, "bonus": {"type": "reward_percent", "value": 0.02}},
    "veteran_miner": {"name": "Miner Veterano", "category": "volume", "icon": "⛏️", "description": "Encontre 1.000 palavras.", "requirement": {"stat": "words_found", "target": 1000}, "bonus": {"type": "reward_percent", "value": 0.03}},
    "master_miner": {"name": "Miner Mestre", "category": "volume", "icon": "⛏️", "description": "Encontre 5.000 palavras.", "requirement": {"stat": "words_found", "target": 5000}, "bonus": {"type": "reward_percent", "value": 0.05}},
    "mempool_legend": {"name": "Lenda da Mempool", "category": "volume", "icon": "⛏️", "description": "Encontre 10.000 palavras.", "requirement": {"stat": "words_found", "target": 10000}, "bonus": {"type": "reward_percent", "value": 0.08}},
    # Raridade — tipos especiais de transacao
    "first_golden": {"name": "Primeiro Golden", "category": "raridade", "icon": "🌟", "description": "Encontre seu primeiro Golden Hash.", "requirement": {"stat": "golden_found", "target": 1}, "bonus": {"type": "reward_percent", "value": 0.02}},
    "golden_hunter": {"name": "Golden Hunter", "category": "raridade", "icon": "🌟", "description": "Encontre 10 Golden Hashes.", "requirement": {"stat": "golden_found", "target": 10}, "bonus": {"type": "reward_percent", "value": 0.03}},
    "first_high_fee": {"name": "Primeiro High Fee", "category": "raridade", "icon": "💎", "description": "Encontre sua primeira transacao High Fee.", "requirement": {"stat": "high_fee_found", "target": 1}, "bonus": {"type": "reward_percent", "value": 0.01}},
    "fee_sniper": {"name": "Fee Sniper", "category": "raridade", "icon": "💎", "description": "Encontre 10 transacoes High Fee.", "requirement": {"stat": "high_fee_found", "target": 10}, "bonus": {"type": "reward_percent", "value": 0.02}},
    "first_mev": {"name": "Primeiro MEV", "category": "raridade", "icon": "🔍", "description": "Encontre sua primeira transacao MEV secreta.", "requirement": {"stat": "mev_found", "target": 1}, "bonus": {"type": "reward_percent", "value": 0.03}},
    "mev_master": {"name": "MEV Master", "category": "raridade", "icon": "🔍", "description": "Encontre 5 transacoes MEV.", "requirement": {"stat": "mev_found", "target": 5}, "bonus": {"type": "reward_percent", "value": 0.05}},
    # Velocidade — combos e velocidade
    "combo_starter": {"name": "Combo Starter", "category": "velocidade", "icon": "⚡", "description": "Atinga seu primeiro combo 2×.", "requirement": {"stat": "combos_2x", "target": 1}, "bonus": {"type": "hint_discount", "value": 0.05}},
    "combo_master": {"name": "Combo Master", "category": "velocidade", "icon": "⚡", "description": "Atinga 50 combos 2× ou superior.", "requirement": {"stat": "combos_2x", "target": 50}, "bonus": {"type": "hint_discount", "value": 0.05}},
    "speed_runner": {"name": "Speed Runner", "category": "velocidade", "icon": "⚡", "description": "Atinga um combo 4×.", "requirement": {"stat": "combos_4x", "target": 1}, "bonus": {"type": "hint_discount", "value": 0.05}},
    "combo_king": {"name": "Combo King", "category": "velocidade", "icon": "⚡", "description": "Atinga 10 combos 4×.", "requirement": {"stat": "combos_4x", "target": 10}, "bonus": {"type": "hint_discount", "value": 0.10}},
    "lightning_fast": {"name": "Lightning Fast", "category": "velocidade", "icon": "⚡", "description": "Encontre uma palavra em menos de 3 segundos.", "requirement": {"stat": "fast_finds", "target": 1}, "bonus": {"type": "hint_discount", "value": 0.05}},
    "speed_demon": {"name": "Speed Demon", "category": "velocidade", "icon": "⚡", "description": "Encontre uma palavra em menos de 2 segundos.", "requirement": {"stat": "ultra_fast_finds", "target": 1}, "bonus": {"type": "hint_discount", "value": 0.08}},
    # Exploracao — realms e blocos
    "first_block": {"name": "Primeiro Bloco", "category": "exploracao", "icon": "🧊", "description": "Complete seu primeiro bloco.", "requirement": {"stat": "blocks_completed", "target": 1}, "bonus": {"type": "reward_percent", "value": 0.01}},
    "block_runner": {"name": "Block Runner", "category": "exploracao", "icon": "🧊", "description": "Complete 10 blocos.", "requirement": {"stat": "blocks_completed", "target": 10}, "bonus": {"type": "reward_percent", "value": 0.02}},
    "block_veteran": {"name": "Block Veteran", "category": "exploracao", "icon": "🧊", "description": "Complete 100 blocos.", "requirement": {"stat": "blocks_completed", "target": 100}, "bonus": {"type": "reward_percent", "value": 0.03}},
    "multi_realm": {"name": "Multi-Realm", "category": "exploracao", "icon": "🌐", "description": "Jogue em 3 realms diferentes.", "requirement": {"stat": "realms_played", "target": 3}, "bonus": {"type": "reward_percent", "value": 0.02}},
    "realm_explorer": {"name": "Realm Explorer", "category": "exploracao", "icon": "🌐", "description": "Jogue em 5 realms diferentes.", "requirement": {"stat": "realms_played", "target": 5}, "bonus": {"type": "reward_percent", "value": 0.04}},
    "epoch_survivor": {"name": "Epoch Survivor", "category": "exploracao", "icon": "🌐", "description": "Sobreviva a 1 epoch completa.", "requirement": {"stat": "epochs_survived", "target": 1}, "bonus": {"type": "reward_percent", "value": 0.03}},
    # Social — pools e leaderboard
    "first_score": {"name": "Primeiro Recorde", "category": "social", "icon": "🏆", "description": "Envie sua primeira pontuacao para o leaderboard.", "requirement": {"stat": "scores_submitted", "target": 1}, "bonus": {"type": "reward_percent", "value": 0.01}},
    "score_climber": {"name": "Score Climber", "category": "social", "icon": "🏆", "description": "Atinga 100.000 sats no leaderboard.", "requirement": {"stat": "max_score", "target": 100000}, "bonus": {"type": "reward_percent", "value": 0.02}},
    "pool_member": {"name": "Pool Member", "category": "social", "icon": "🤝", "description": "Entre em uma mining pool.", "requirement": {"stat": "pool_joined", "target": 1}, "bonus": {"type": "reward_percent", "value": 0.02}},
    "top_10": {"name": "Top 10", "category": "social", "icon": "🏆", "description": "Entre no top 10 do leaderboard.", "requirement": {"stat": "best_rank", "target": 10}, "bonus": {"type": "reward_percent", "value": 0.03}},
    "top_3": {"name": "Top 3", "category": "social", "icon": "🏆", "description": "Entre no top 3 do leaderboard.", "requirement": {"stat": "best_rank", "target": 3}, "bonus": {"type": "reward_percent", "value": 0.05}},
    "pool_leader": {"name": "Pool Leader", "category": "social", "icon": "🤝", "description": "Lidere uma mining pool no ranking.", "requirement": {"stat": "pool_rank_1", "target": 1}, "bonus": {"type": "reward_percent", "value": 0.05}},
}

# Mapeamento stat -> campo para consulta rapida
ACHIEVEMENT_CATEGORIES = {
    "volume": {"name": "Volume", "icon": "⛏️"},
    "raridade": {"name": "Raridade", "icon": "🌟"},
    "velocidade": {"name": "Velocidade", "icon": "⚡"},
    "exploracao": {"name": "Exploracao", "icon": "🧊"},
    "social": {"name": "Social", "icon": "🏆"},
}


class StatsUpdate(BaseModel):
    """Atualizacao de stats para tracking de achievements."""

    model_config = ConfigDict(extra="forbid")

    username: Username
    words_found: int | None = None
    golden_found: int | None = None
    high_fee_found: int | None = None
    mev_found: int | None = None
    combos_2x: int | None = None
    combos_4x: int | None = None
    fast_finds: int | None = None
    ultra_fast_finds: int | None = None
    blocks_completed: int | None = None
    realms_played: int | None = None
    epochs_survived: int | None = None
    scores_submitted: int | None = None
    max_score: int | None = None
    pool_joined: int | None = None
    best_rank: int | None = None
    pool_rank_1: int | None = None
    rbf_used: int | None = None
    max_round_earnings: int | None = None


def _check_achievement(stat_value: int, requirement: dict[str, Any]) -> bool:
    """Verifica se um stat atende o requisito de um achievement."""
    target = requirement.get("target", 999999)
    # Para best_rank, menor e melhor (top 3 < top 10)
    stat_name = requirement.get("stat", "")
    if stat_name == "best_rank":
        return stat_value > 0 and stat_value <= target
    return stat_value >= target


async def _get_player_stats(realm_id: str, username: str) -> dict[str, int]:
    """Carrega os stats do jogador do Redis."""
    key = player_stats_key(realm_id, username)
    raw = await redis_client.hgetall(key)
    stats = {}
    for stat_name, stat_value in raw.items():
        try:
            stats[stat_name] = int(stat_value)
        except (ValueError, TypeError):
            stats[stat_name] = 0
    return stats


async def _get_unlocked_achievements(realm_id: str, username: str) -> set[str]:
    """Carrega os achievements ja desbloqueados do jogador."""
    key = achievements_key(realm_id, username)
    raw = await redis_client.hgetall(key)
    return {k for k, v in raw.items() if v == "1"}


async def _check_and_unlock_achievements(realm_id: str, username: str, stats: dict[str, int]) -> list[str]:
    """Verifica todos os achievements e desbloqueia os que foram atingidos.

    Returns:
        Lista de IDs de achievements novemente desbloqueados.
    """
    unlocked = await _get_unlocked_achievements(realm_id, username)
    newly_unlocked = []
    key = achievements_key(realm_id, username)

    for ach_id, ach_def in ACHIEVEMENTS.items():
        if ach_id in unlocked:
            continue
        req = ach_def["requirement"]
        stat_name = req["stat"]
        stat_value = stats.get(stat_name, 0)
        if _check_achievement(stat_value, req):
            await redis_client.hset(key, ach_id, "1")
            await redis_client.expire(key, 86400)
            newly_unlocked.append(ach_id)
            logger.info(
                "Achievement desbloqueado: %s para %s em %s",
                ach_id, username, realm_id,
            )

    return newly_unlocked


async def _calculate_achievement_bonuses(realm_id: str, username: str) -> dict[str, Any]:
    """Calcula os bônus acumulados dos achievements desbloqueados."""
    unlocked = await _get_unlocked_achievements(realm_id, username)
    reward_percent = 0.0
    hint_discount = 0.0

    for ach_id in unlocked:
        ach_def = ACHIEVEMENTS.get(ach_id)
        if not ach_def:
            continue
        bonus = ach_def.get("bonus", {})
        bonus_type = bonus.get("type", "")
        bonus_value = bonus.get("value", 0)
        if bonus_type == "reward_percent":
            reward_percent += bonus_value
        elif bonus_type == "hint_discount":
            hint_discount += bonus_value

    return {
        "reward_percent": round(reward_percent, 4),
        "hint_discount": round(hint_discount, 4),
    }


@app.get("/api/v1/networks/{realm_id}/achievements/{username}", tags=["Achievements"])
async def get_achievements(realm_id: str, username: str) -> dict[str, Any]:
    """Retorna a lista de achievements com status e progresso.

    Args:
        realm_id: Identificador do realm.
        username: Nome do minerador.

    Returns:
        Dict com achievements, bônus ativos e stats atuais.
    """
    definition = get_network_definition(realm_id)
    stats = await _get_player_stats(definition.realm_id, username)
    unlocked = await _get_unlocked_achievements(definition.realm_id, username)
    bonuses = await _calculate_achievement_bonuses(definition.realm_id, username)

    achievements_list = []
    for ach_id, ach_def in ACHIEVEMENTS.items():
        req = ach_def["requirement"]
        stat_name = req["stat"]
        stat_value = stats.get(stat_name, 0)
        target = req["target"]
        is_unlocked = ach_id in unlocked

        # Calcula progresso (0.0 a 1.0)
        if stat_name == "best_rank":
            progress = 1.0 if (stat_value > 0 and stat_value <= target) else min(stat_value / max(target, 1), 1.0) if stat_value > 0 else 0.0
        else:
            progress = min(stat_value / target, 1.0)

        achievements_list.append({
            "id": ach_id,
            "name": ach_def["name"],
            "category": ach_def["category"],
            "icon": ach_def["icon"],
            "description": ach_def["description"],
            "unlocked": is_unlocked,
            "progress": round(progress, 4),
            "current": stat_value,
            "target": target,
            "bonus": ach_def.get("bonus", {}),
        })

    return {
        "realm_id": definition.realm_id,
        "username": username,
        "achievements": achievements_list,
        "bonuses": bonuses,
        "stats": stats,
    }


@app.post("/api/v1/networks/{realm_id}/stats/{username}", tags=["Achievements"])
async def update_stats(realm_id: str, username: str, data: StatsUpdate) -> dict[str, Any]:
    """Atualiza os stats do jogador e verifica achievements.

    Args:
        realm_id: Identificador do realm.
        username: Nome do minerador.
        data: Stats a atualizar.

    Returns:
        Dict com stats atualizados e achievements novemente desbloqueados.
    """
    username = matching_username(username, data.username)
    definition = get_network_definition(realm_id)
    stats_key = player_stats_key(definition.realm_id, username)
    updates = data.model_dump(exclude={"username"}, exclude_none=True)

    if updates:
        await redis_client.hset(stats_key, mapping=updates)
        await redis_client.expire(stats_key, 86400)

    stats = await _get_player_stats(definition.realm_id, username)
    newly_unlocked = await _check_and_unlock_achievements(definition.realm_id, username, stats)
    bonuses = await _calculate_achievement_bonuses(definition.realm_id, username)

    return {
        "realm_id": definition.realm_id,
        "username": username,
        "stats": stats,
        "newly_unlocked": newly_unlocked,
        "bonuses": bonuses,
    }


@app.get("/api/v1/networks/{realm_id}/achievements/definitions", tags=["Achievements"])
async def get_achievements_definitions() -> dict[str, Any]:
    """Retorna as definicoes de todos os achievements (sem dados do jogador).

    Returns:
        Dict com categorias e lista de achievements.
    """
    return {
        "categories": ACHIEVEMENT_CATEGORIES,
        "achievements": [
            {
                "id": ach_id,
                "name": ach_def["name"],
                "category": ach_def["category"],
                "icon": ach_def["icon"],
                "description": ach_def["description"],
                "requirement": ach_def["requirement"],
                "bonus": ach_def.get("bonus", {}),
            }
            for ach_id, ach_def in ACHIEVEMENTS.items()
        ],
    }


@app.get("/api/v1/networks/{realm_id}/missions/{username}", tags=["Missões"])
async def get_missions(realm_id: str, username: str) -> dict[str, Any]:
    """Retorna a lista de missões diárias e semanal com progresso atual.

    Missões diárias (3 rotativas, reset à meia-noite UTC):
    - "Encontre 5 palavras High Fee" → 2.000 sats
    - "Ganhe 50K sats em uma rodada" → 3.000 sats
    - "Use RBF com sucesso" → 5.000 sats
    - "Encontre 3 palavras MEV" → 10.000 sats
    - "Complete 3 blocos seguidos" → 4.000 sats
    - "Acerte 10 palavras sem erro" → 2.500 sats

    Missão semanal (reset aos domingos UTC):
    - "Encontre 100 palavras na semana" → 50.000 sats + achievement especial

    Args:
        realm_id: Identificador do realm.
        username: Nome do minerador.

    Returns:
        Dict com missões diárias e semanal, cada uma com progresso, recompensa e status.
    """
    definition = get_network_definition(realm_id)
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    today = now_utc.strftime("%Y-%m-%d")
    # ISO week: ano-ISO, semana-ISO, dia-da-semana (1=segunda, 7=domingo)
    iso_cal = now_utc.isocalendar()
    week_key = f"{iso_cal[0]}-W{iso_cal[1]:02d}"

    # Carrega progresso diário do Redis
    daily_key = missions_key(definition.realm_id, username, today)
    daily_raw = await redis_client.hgetall(daily_key)

    # Carrega progresso semanal do Redis
    weekly_key = weekly_missions_key(definition.realm_id, username, week_key)
    weekly_raw = await redis_client.hgetall(weekly_key)

    # Definição das missões diárias
    daily_mission_defs = [
        {
            "id": "find_5_high_fee",
            "title": "Encontre 5 palavras High Fee",
            "description": "Encontre 5 transações High Fee na mempool.",
            "target": 5,
            "stat": "high_fee_found",
            "reward": 2000,
            "type": "daily",
        },
        {
            "id": "earn_50k_round",
            "title": "Ganhe 50K sats em uma rodada",
            "description": "Acumule 50.000 sats em uma única rodada.",
            "target": 50000,
            "stat": "max_round_earnings",
            "reward": 3000,
            "type": "daily",
        },
        {
            "id": "use_rbf",
            "title": "Use RBF com sucesso",
            "description": "Ative o RBF para resgatar um bloco órfão.",
            "target": 1,
            "stat": "rbf_used",
            "reward": 5000,
            "type": "daily",
        },
        {
            "id": "find_3_mev",
            "title": "Encontre 3 palavras MEV",
            "description": "Encontre 3 transações MEV secretas.",
            "target": 3,
            "stat": "mev_found",
            "reward": 10000,
            "type": "daily",
        },
        {
            "id": "complete_3_blocks",
            "title": "Complete 3 blocos seguidos",
            "description": "Complete 3 blocos sem falhar nenhum.",
            "target": 3,
            "stat": "blocks_completed",
            "reward": 4000,
            "type": "daily",
        },
        {
            "id": "10_words_no_error",
            "title": "Acerte 10 palavras sem erro",
            "description": "Encontre 10 palavras consecutivas sem erro.",
            "target": 10,
            "stat": "words_found",
            "reward": 2500,
            "type": "daily",
        },
    ]

    # Seleciona 3 missões diárias rotativas baseadas no dia do ano
    day_of_year = now_utc.timetuple().tm_yday
    rotation_index = day_of_year % 3
    daily_selection = [
        daily_mission_defs[rotation_index * 2],
        daily_mission_defs[rotation_index * 2 + 1],
        daily_mission_defs[(rotation_index * 2 + 2) % len(daily_mission_defs)],
    ]

    # Constrói missões diárias com progresso
    daily_missions = []
    for mission_def in daily_selection:
        mission_id = mission_def["id"]
        stat_name = mission_def["stat"]
        target = mission_def["target"]
        reward = mission_def["reward"]

        # Verifica se a missão foi completada e recompensa coletada
        completed_key = f"completed:{mission_id}"
        claimed_key = f"claimed:{mission_id}"

        is_completed = daily_raw.get(completed_key) == "1"
        is_claimed = daily_raw.get(claimed_key) == "1"

        # Progresso: usa o stat do player_stats se disponível
        stats = await _get_player_stats(definition.realm_id, username)
        current_progress = stats.get(stat_name, 0)

        # Se a missão específica tem progresso salvo no hash diário, usa ele
        progress_field = f"progress:{mission_id}"
        if progress_field in daily_raw:
            try:
                current_progress = int(daily_raw[progress_field])
            except (ValueError, TypeError):
                current_progress = stats.get(stat_name, 0)

        progress = min(current_progress / target, 1.0)

        daily_missions.append({
            "id": mission_id,
            "title": mission_def["title"],
            "description": mission_def["description"],
            "target": target,
            "current": current_progress,
            "reward": reward,
            "progress": round(progress, 4),
            "completed": is_completed,
            "claimed": is_claimed,
            "type": "daily",
        })

    # Missão semanal
    weekly_mission_def = {
        "id": "find_100_words_week",
        "title": "Encontre 100 palavras na semana",
        "description": "Encontre 100 palavras na mempool durante a semana.",
        "target": 100,
        "stat": "words_found",
        "reward": 50000,
        "type": "weekly",
        "achievement": "weekly_miner_champion",
    }

    weekly_mission_id = weekly_mission_def["id"]
    weekly_completed_key = f"completed:{weekly_mission_id}"
    weekly_claimed_key = f"claimed:{weekly_mission_id}"

    weekly_is_completed = weekly_raw.get(weekly_completed_key) == "1"
    weekly_is_claimed = weekly_raw.get(weekly_claimed_key) == "1"

    weekly_stats = await _get_player_stats(definition.realm_id, username)
    weekly_progress_val = weekly_stats.get("words_found", 0)

    weekly_progress_field = f"progress:{weekly_mission_id}"
    if weekly_progress_field in weekly_raw:
        try:
            weekly_progress_val = int(weekly_raw[weekly_progress_field])
        except (ValueError, TypeError):
            pass

    weekly_progress = min(weekly_progress_val / weekly_mission_def["target"], 1.0)

    weekly_mission = {
        "id": weekly_mission_id,
        "title": weekly_mission_def["title"],
        "description": weekly_mission_def["description"],
        "target": weekly_mission_def["target"],
        "current": weekly_progress_val,
        "reward": weekly_mission_def["reward"],
        "progress": round(weekly_progress, 4),
        "completed": weekly_is_completed,
        "claimed": weekly_is_claimed,
        "type": "weekly",
        "achievement": weekly_mission_def.get("achievement"),
    }

    return {
        "realm_id": definition.realm_id,
        "username": username,
        "daily_missions": daily_missions,
        "weekly_mission": weekly_mission,
        "reset_info": {
            "daily_reset": "00:00 UTC",
            "weekly_reset": "Domingo 00:00 UTC",
            "current_date": today,
            "current_week": week_key,
        },
    }


@app.post("/api/v1/networks/{realm_id}/missions/{username}/claim/{mission_id}", tags=["Missões"])
async def claim_mission_reward(realm_id: str, username: str, mission_id: str) -> dict[str, Any]:
    """Reclama a recompensa de uma missão completada.

    Args:
        realm_id: Identificador do realm.
        username: Nome do minerador.
        mission_id: ID da missão a reclamar.

    Returns:
        Dict com status e recompensa obtida.
    """
    definition = get_network_definition(realm_id)
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    today = now_utc.strftime("%Y-%m-%d")
    iso_cal = now_utc.isocalendar()
    week_key = f"{iso_cal[0]}-W{iso_cal[1]:02d}"

    # Determina se é diária ou semanal
    is_weekly = mission_id in {
        "find_100_words_week",
    }

    if is_weekly:
        key = weekly_missions_key(definition.realm_id, username, week_key)
    else:
        key = missions_key(definition.realm_id, username, today)

    # Verifica se a missão foi completada
    completed_key = f"completed:{mission_id}"
    claimed_key = f"claimed:{mission_id}"

    is_completed = await redis_client.hget(key, completed_key) == "1"
    is_claimed = await redis_client.hget(key, claimed_key) == "1"

    if not is_completed:
        raise HTTPException(status_code=400, detail="Missão não completada")
    if is_claimed:
        raise HTTPException(status_code=400, detail="Recompensa já coletada")

    # Define recompensas
    rewards = {
        "find_5_high_fee": 2000,
        "earn_50k_round": 3000,
        "use_rbf": 5000,
        "find_3_mev": 10000,
        "complete_3_blocks": 4000,
        "10_words_no_error": 2500,
        "find_100_words_week": 50000,
    }

    reward_amount = rewards.get(mission_id, 0)
    if reward_amount == 0:
        raise HTTPException(status_code=404, detail="Missão não encontrada")

    # Marca como reclamada
    await redis_client.hset(key, claimed_key, "1")
    await redis_client.expire(key, 86400 * 8)  # 8 dias TTL

    # Adiciona ao saldo do jogador
    state_key = player_state_key(definition.realm_id, username)
    await redis_client.hincrby(state_key, "balance", reward_amount)
    await redis_client.expire(state_key, 86400)

    logger.info(
        "Recompensa coletada: %d sats para %s em %s (missão: %s)",
        reward_amount, username, definition.realm_id, mission_id,
    )

    return {
        "status": "success",
        "reward": reward_amount,
        "mission_id": mission_id,
        "username": username,
    }


@app.post("/api/v1/networks/{realm_id}/missions/{username}/update", tags=["Missões"])
async def update_mission_progress(
    realm_id: str,
    username: str,
    data: StatsUpdate,
) -> dict[str, Any]:
    """Atualiza o progresso das missões com base nos stats do jogador.

    Args:
        realm_id: Identificador do realm.
        username: Nome do minerador.
        data: Stats a atualizar.

    Returns:
        Dict com missões atualizadas e novas completadas.
    """
    username = matching_username(username, data.username)
    definition = get_network_definition(realm_id)
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    today = now_utc.strftime("%Y-%m-%d")
    iso_cal = now_utc.isocalendar()
    week_key = f"{iso_cal[0]}-W{iso_cal[1]:02d}"

    stats_key = player_stats_key(definition.realm_id, username)
    updates = data.model_dump(exclude={"username"}, exclude_none=True)

    if updates:
        await redis_client.hset(stats_key, mapping=updates)
        await redis_client.expire(stats_key, 86400)

    # Atualiza progresso diário
    daily_key = missions_key(definition.realm_id, username, today)
    newly_completed_daily = []

    daily_mission_stats = {
        "find_5_high_fee": "high_fee_found",
        "earn_50k_round": "max_round_earnings",
        "use_rbf": "rbf_used",
        "find_3_mev": "mev_found",
        "complete_3_blocks": "blocks_completed",
        "10_words_no_error": "words_found",
    }

    for mission_id, stat_name in daily_mission_stats.items():
        completed_key = f"completed:{mission_id}"
        claimed_key = f"claimed:{mission_id}"
        progress_field = f"progress:{mission_id}"

        # Pula se já reclamada
        if await redis_client.hget(daily_key, claimed_key) == "1":
            continue

        current_val = updates.get(stat_name, 0)
        if current_val == 0:
            stats = await _get_player_stats(definition.realm_id, username)
            current_val = stats.get(stat_name, 0)

        await redis_client.hset(daily_key, progress_field, str(current_val))

        # Verifica completude (thresholds variam por missão)
        target = {
            "find_5_high_fee": 5,
            "earn_50k_round": 50000,
            "use_rbf": 1,
            "find_3_mev": 3,
            "complete_3_blocks": 3,
            "10_words_no_error": 10,
        }.get(mission_id, 1)

        if current_val >= target and await redis_client.hget(daily_key, completed_key) != "1":
            await redis_client.hset(daily_key, completed_key, "1")
            newly_completed_daily.append(mission_id)

    # Atualiza progresso semanal
    weekly_key = weekly_missions_key(definition.realm_id, username, week_key)
    weekly_progress_field = "progress:find_100_words_week"
    weekly_completed_key = "completed:find_100_words_week"
    weekly_claimed_key = "claimed:find_100_words_week"

    weekly_val = updates.get("words_found", 0)
    if weekly_val == 0:
        stats = await _get_player_stats(definition.realm_id, username)
        weekly_val = stats.get("words_found", 0)

    await redis_client.hset(weekly_key, weekly_progress_field, str(weekly_val))

    newly_completed_weekly = []
    if weekly_val >= 100 and await redis_client.hget(weekly_key, weekly_completed_key) != "1":
        await redis_client.hset(weekly_key, weekly_completed_key, "1")
        newly_completed_weekly.append("find_100_words_week")

    return {
        "realm_id": definition.realm_id,
        "username": username,
        "newly_completed_daily": newly_completed_daily,
        "newly_completed_weekly": newly_completed_weekly,
    }


# Fase 10: Skill Tree — árvore de habilidades do jogador
# ==========================================================================

# Definições dos ramos de habilidades
SKILL_BRANCHES: dict[str, dict[str, Any]] = {
    "mining": {
        "name": "Mining",
        "icon": "⛏️",
        "color": "var(--btc-orange)",
        "levels": [
            {"level": 1, "name": "Tempo Base +1s", "description": "+1s de tempo base por rodada."},
            {"level": 2, "name": "Tempo Base +2s", "description": "+2s de tempo base por rodada."},
            {"level": 3, "name": "Tempo Base +3s", "description": "+3s de tempo base por rodada."},
            {"level": 4, "name": "Tempo Base +4s", "description": "+4s de tempo base por rodada."},
            {"level": 5, "name": "Tempo Base +5s", "description": "+5s de tempo base por rodada."},
        ],
    },
    "search": {
        "name": "Search",
        "icon": "🔍",
        "color": "var(--hint-yellow)",
        "levels": [
            {"level": 1, "name": "Hints -10%", "description": "Dicas 10% mais baratas."},
            {"level": 2, "name": "Hints -20%", "description": "Dicas 20% mais baratas."},
            {"level": 3, "name": "Hints -30%", "description": "Dicas 30% mais baratas."},
            {"level": 4, "name": "Hints -40%", "description": "Dicas 40% mais baratas."},
            {"level": 5, "name": "Hints -50%", "description": "Dicas 50% mais baratas."},
        ],
    },
    "lightning": {
        "name": "Lightning",
        "icon": "⚡",
        "color": "var(--lightning-blue)",
        "levels": [
            {"level": 1, "name": "+5% Recompensa", "description": "+5% na recompensa base."},
            {"level": 2, "name": "+10% Recompensa", "description": "+10% na recompensa base."},
            {"level": 3, "name": "+15% Recompensa", "description": "+15% na recompensa base."},
            {"level": 4, "name": "+20% Recompensa", "description": "+20% na recompensa base."},
            {"level": 5, "name": "+25% Recompensa", "description": "+25% na recompensa base."},
        ],
    },
}


class SkillUpgradeRequest(BaseModel):
    """Solicitação de upgrade de habilidade."""

    model_config = ConfigDict(extra="forbid")

    username: Username
    branch: str = Field(min_length=1, max_length=20)


def _calculate_skill_points(player_level: int) -> int:
    """Calcula pontos de habilidade acumulados com base no nível do jogador.

    1 ponto a cada 10 níveis (nível 10 = 1 ponto, nível 20 = 2 pontos, etc.).
    """
    return player_level // 10


def _get_skill_bonuses(
    mining_level: int,
    search_level: int,
    lightning_level: int,
) -> dict[str, Any]:
    """Calcula os bônus ativos com base nos níveis de habilidade."""
    return {
        "mining_time_bonus": mining_level,  # +N segundos
        "search_discount_percent": search_level * 10,  # N*10% desconto
        "lightning_reward_percent": lightning_level * 5,  # N*5% bônus
    }


@app.get("/api/v1/networks/{realm_id}/skills/{username}", tags=["Skill Tree"])
async def get_skills(realm_id: str, username: str) -> dict[str, Any]:
    """Retorna a árvore de habilidades do jogador com status atual.

    Args:
        realm_id: Identificador do realm.
        username: Nome do minerador.

    Returns:
        Dict com ramos de habilidades, níveis atuais, pontos disponíveis
        e bônus calculados.
    """
    definition = get_network_definition(realm_id)

    # Obtém nível do jogador para calcular pontos totais
    lvl_key = level_key(definition.realm_id, username)
    lvl_raw = await redis_client.hget(lvl_key, "level")
    player_level = int(lvl_raw) if lvl_raw else 1
    total_points = _calculate_skill_points(player_level)

    # Carrega estado das habilidades do Redis
    sk_key = skills_key(definition.realm_id, username)
    raw = await redis_client.hgetall(sk_key)

    mining_level = int(raw.get("mining_level", 0))
    search_level = int(raw.get("search_level", 0))
    lightning_level = int(raw.get("lightning_level", 0))
    points_remaining = int(raw.get("points_remaining", 0))

    # Garante consistência: se o jogador subiu de nível, recalcula pontos
    spent = mining_level + search_level + lightning_level
    expected_remaining = total_points - spent
    if expected_remaining > points_remaining:
        # Jogador ganhou pontos novos (subiu de nível)
        await redis_client.hset(sk_key, "points_remaining", str(expected_remaining))
        await redis_client.expire(sk_key, 86400)
        points_remaining = expected_remaining

    bonuses = _get_skill_bonuses(mining_level, search_level, lightning_level)

    # Constrói resposta com cada ramo e seus nós
    branches = {}
    for branch_key, branch_def in SKILL_BRANCHES.items():
        current_level = {
            "mining": mining_level,
            "search": search_level,
            "lightning": lightning_level,
        }[branch_key]

        nodes = []
        for lvl_def in branch_def["levels"]:
            lvl = lvl_def["level"]
            unlocked = lvl <= current_level
            nodes.append({
                "level": lvl,
                "name": lvl_def["name"],
                "description": lvl_def["description"],
                "unlocked": unlocked,
            })

        branches[branch_key] = {
            "name": branch_def["name"],
            "icon": branch_def["icon"],
            "color": branch_def["color"],
            "current_level": current_level,
            "max_level": 5,
            "nodes": nodes,
        }

    return {
        "realm_id": definition.realm_id,
        "username": username,
        "player_level": player_level,
        "total_skill_points": total_points,
        "points_remaining": points_remaining,
        "branches": branches,
        "bonuses": bonuses,
    }


@app.post("/api/v1/networks/{realm_id}/skills/{username}/upgrade", tags=["Skill Tree"])
async def upgrade_skill(realm_id: str, username: str, data: SkillUpgradeRequest) -> dict[str, Any]:
    """Desbloqueia o próximo nível em um ramo de habilidade.

    Consome 1 ponto de habilidade. O jogador precisa ter pontos disponíveis
    e o ramo não pode estar no nível máximo.

    Args:
        realm_id: Identificador do realm.
        username: Nome do minerador.
        data: Payload com ``branch`` (mining, search, ou lightning).

    Returns:
        Estado atualizado da árvore de habilidades.

    Raises:
        HTTPException: Se o ramo for inválido, o jogador não tiver pontos,
                       ou o ramo já estiver no máximo (400).
    """
    definition = get_network_definition(realm_id)

    # Valida ramo
    if data.branch not in SKILL_BRANCHES:
        raise HTTPException(
            status_code=400,
            detail=f"Ramo inválido: {data.branch}. Use: mining, search, lightning",
        )

    sk_key = skills_key(definition.realm_id, username)
    raw = await redis_client.hgetall(sk_key)

    branch_level_key = f"{data.branch}_level"
    current_level = int(raw.get(branch_level_key, 0))

    # Verifica se já está no máximo
    if current_level >= 5:
        raise HTTPException(status_code=400, detail=f"Ramo {data.branch} já está no nível máximo (5)")

    # Verifica pontos disponíveis
    points_remaining = int(raw.get("points_remaining", 0))
    if points_remaining < 1:
        raise HTTPException(status_code=400, detail="Pontos de habilidade insuficientes")

    # Obtém nível do jogador para recalcular pontos
    lvl_key = level_key(definition.realm_id, username)
    lvl_raw = await redis_client.hget(lvl_key, "level")
    player_level = int(lvl_raw) if lvl_raw else 1
    total_points = _calculate_skill_points(player_level)

    # Atualiza atomicamente: incrementa nível do ramo, decrementa pontos
    pipe = redis_client.pipeline()
    pipe.hincrby(sk_key, branch_level_key, 1)
    pipe.hincrby(sk_key, "points_remaining", -1)
    pipe.expire(sk_key, 86400)
    results = await pipe.execute()

    new_level = current_level + 1
    new_points = points_remaining - 1

    logger.info(
        "Skill upgrade: %s -> %s nível %d (pontos restantes: %d)",
        username, data.branch, new_level, new_points,
    )

    # Retorna estado atualizado
    return await get_skills(realm_id, username)


# Fase 1: Relay persistente — subscreve ao PubSub independentemente de conexões WebSocket.
# Cada realm tem seu próprio relay, que armazena eventos em uma fila interna.
# Quando um WebSocket conecta, recebe eventos da fila do relay.

_event_relays: dict[str, "EventRelay"] = {}


class EventRelay:
    """Relay persistente que subscreve ao canal PubSub do Redis e distribui eventos
    para múltiplas conexões WebSocket simultâneas.

    O relay é criado quando o primeiro WebSocket conecta e encerrado quando
    o último desconecta. Eventos são armazenados em uma fila interna com
    limite de 1000 itens para evitar consumo excessivo de memória.
    """

    def __init__(self, realm_id: str) -> None:
        self.realm_id = realm_id
        self.queue: asyncio.Queue[str] = asyncio.Queue(maxsize=1000)
        self.pubsub = redis_client.pubsub()
        self._listen_task: asyncio.Task[None] | None = None
        self._subscribed = False

    async def start(self) -> None:
        """Subscreve ao canal de eventos e inicia o listener."""
        if self._subscribed:
            return
        channel = events_channel(self.realm_id)
        await self.pubsub.subscribe(channel)
        self._listen_task = asyncio.create_task(
            self._listen(),
            name=f"relay-listener-{self.realm_id}",
        )
        self._subscribed = True
        logger.info("Relay persistente iniciado para %s", self.realm_id)

    async def _listen(self) -> None:
        """Escuta o canal PubSub e armazena eventos na fila interna."""
        async for message in self.pubsub.listen():
            if message["type"] == "message":
                try:
                    self.queue.put_nowait(message["data"])
                    logger.debug("Relay %s: evento recebido (fila=%d)", self.realm_id, self.queue.qsize())
                except asyncio.QueueFull:
                    logger.warning(
                        "Fila do relay cheia para %s; evento descartado",
                        self.realm_id,
                    )

    async def stop(self) -> None:
        """Encerra o listener e a subscrição PubSub."""
        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        if self._subscribed:
            await self.pubsub.unsubscribe()
            await self.pubsub.aclose()
            self._subscribed = False
        logger.info("Relay persistente encerrado para %s", self.realm_id)


async def get_relay(realm_id: str) -> EventRelay:
    """Obtém ou cria o relay persistente para um realm."""
    if realm_id not in _event_relays:
        relay = EventRelay(realm_id)
        await relay.start()
        _event_relays[realm_id] = relay
    return _event_relays[realm_id]


async def release_relay(realm_id: str) -> None:
    """Encerra o relay persistente se não houver mais conexões WebSocket."""
    relay = _event_relays.pop(realm_id, None)
    if relay:
        await relay.stop()


async def ws_sender(
    websocket: WebSocket,
    realm_id: str,
    relay: EventRelay,
    heartbeat_interval: int = 30,
) -> None:
    """Repassa somente campos públicos de eventos pertencentes ao realm.

    Envia heartbeat periódico (a cada ``heartbeat_interval`` segundos) quando
    não há atividade no stream, permitindo que o cliente detecte inatividade.

    Args:
        websocket: Conexão WebSocket aceita.
        realm_id: Realm para filtrar eventos.
        relay: Relay persistente que fornece eventos do PubSub.
        heartbeat_interval: Intervalo em segundos para enviar heartbeat.
    """
    last_activity = asyncio.get_event_loop().time()
    while True:
        try:
            # Aguarda evento da fila do relay com timeout para heartbeat
            try:
                raw_event = await asyncio.wait_for(relay.queue.get(), timeout=heartbeat_interval)
            except asyncio.TimeoutError:
                # Heartbeat: se não houve atividade há mais que o intervalo,
                # envia ping para manter a conexão viva.
                try:
                    await websocket.send_text(
                        json.dumps({"action": "heartbeat"}, separators=(",", ":"))
                    )
                except RuntimeError:
                    # WebSocket já fechado — encerra o sender.
                    return
                last_activity = asyncio.get_event_loop().time()
                continue

            last_activity = asyncio.get_event_loop().time()
            serialized = serialize_public_event(raw_event, realm_id)
            if serialized is None:
                logger.debug("Evento Redis fora do contrato público foi ignorado")
                continue
            await websocket.send_text(serialized)
        except RuntimeError:
            # WebSocket já fechado — encerra o sender.
            return


async def ws_receiver(websocket: WebSocket, realm_id: str) -> None:
    """Mantém a conexão aberta e detecta o desligamento do navegador.

    Usa timeout de 5 minutos para evitar conexões órfãs que nunca
    recebem o ``websocket.disconnect`` (ex: network partition, kill -9).

    Fase 11: Processa mensagens de heartbeat do cliente para tracking online.
    """
    while True:
        try:
            message: dict[str, Any] = await asyncio.wait_for(
                websocket.receive(), timeout=300
            )
        except asyncio.TimeoutError:
            # Cliente inativo por 5 minutos — encerra a conexão.
            logger.debug("WebSocket receiver timeout; encerrando conexao")
            return
        if message["type"] == "websocket.disconnect":
            return
        # Fase 11: Heartbeat do jogador — atualiza status online
        if message["type"] == "websocket.text":
            try:
                text = message.get("text", "")
                payload = json.loads(text)
                if isinstance(payload, dict) and payload.get("action") == "player_heartbeat":
                    username = payload.get("username")
                    if isinstance(username, str) and username.strip():
                        online_hash = online_key(realm_id)
                        now = datetime.datetime.now(datetime.timezone.utc).timestamp()
                        await redis_client.hset(online_hash, username, str(now))
                        await redis_client.expire(online_hash, 86400)
            except (json.JSONDecodeError, TypeError, redis.RedisError):
                pass


async def serve_websocket(websocket: WebSocket, realm_id: str) -> None:
    """Entrega handshake e apenas eventos pertencentes ao realm solicitado.

    Fluxo:
    1. Valida a origem do WebSocket contra ``ALLOWED_ORIGINS``.
    2. Resolve o ``realm_id`` no catálogo de redes.
    3. Aceita a conexão e subscreve ao canal Redis do realm.
    4. Envia ``game_start`` com o snapshot inicial.
    5. Inicia ``ws_sender`` e ``ws_receiver`` em paralelo.

    Args:
        websocket: Conexão WebSocket pendente.
        realm_id: Realm solicitado pelo cliente.
    """
    if not websocket_origin_allowed(websocket):
        logger.warning("WebSocket rejeitado: origem não permitida %s", websocket.headers.get("origin"))
        await websocket.close(code=1008, reason="Origem não permitida")
        return

    try:
        definition = get_network_definition(realm_id)
    except HTTPException:
        logger.warning("WebSocket rejeitado: rede não encontrada %s", realm_id)
        await websocket.close(code=1008, reason="Rede não encontrada")
        return

    await websocket.accept()
    logger.info("WebSocket aceito para %s (origin=%s)", realm_id, websocket.headers.get("origin"))
    sender_task: asyncio.Task[None] | None = None
    receiver_task: asyncio.Task[None] | None = None

    # Fase 1: Obter relay persistente (subscrição PubSub compartilhada)
    relay = await get_relay(definition.realm_id)

    try:
        snapshot = await network_snapshot(definition.realm_id, include_runtime_epoch=True)
        event = event_envelope(
            action="game_start",
            node_id=definition.node_id,
            network=definition.network,
            realm_id=definition.realm_id,
            epoch=snapshot.get("epoch"),
        )
        event.update(
            {
                "status": snapshot["status"],
                "playable": snapshot["playable"],
                "initial_block_download": snapshot["initial_block_download"],
                "verification_progress": snapshot["verification_progress"],
                "pruned": snapshot["pruned"],
            }
        )
        public_event = sanitize_public_event(event, definition.realm_id)
        if public_event is None:  # pragma: no cover - contrato construído localmente
            raise RuntimeError("Falha ao montar evento inicial")
        try:
            await websocket.send_text(json.dumps(public_event, separators=(",", ":")))
            logger.info("game_start enviado para %s", realm_id)
        except Exception as exc:
            logger.warning("Cliente desconectou durante o handshake WebSocket: %s", exc)
            return

        sender_task = asyncio.create_task(
            ws_sender(websocket, definition.realm_id, relay),
            name=f"ws-sender-{definition.realm_id}",
        )
        receiver_task = asyncio.create_task(ws_receiver(websocket, definition.realm_id))
        done, pending = await asyncio.wait(
            {sender_task, receiver_task}, return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        for task in done:
            if not task.cancelled() and task.exception():
                logger.debug("Conexão WebSocket encerrada: %s", task.exception())
    finally:
        for task in (sender_task, receiver_task):
            if task and not task.done():
                task.cancel()




# ==========================================================================
# Fase 8: Power-ups Temporários — inventário e ativação
# ==========================================================================

# Definições de power-ups: id, nome, ícone, preço, duração (segundos), tipo
POWERUP_DEFINITIONS: dict[str, dict[str, Any]] = {
    "time_freeze": {
        "id": "time_freeze",
        "name": "Time Freeze",
        "icon": "⏸️",
        "description": "Pausa o timer por 5 segundos.",
        "price": 10000,
        "duration": 5,
        "type": "timer",
    },
    "scanner": {
        "id": "scanner",
        "name": "Scanner",
        "icon": "🔍",
        "description": "Revela a direção de uma palavra por 1 rodada.",
        "price": 5000,
        "duration": 0,  # 0 = dura até o fim da rodada
        "type": "round",
    },
    "double_combo": {
        "id": "double_combo",
        "name": "Double Combo",
        "icon": "💎",
        "description": "Combo sobe até 6× ao invés de 4× por 1 rodada.",
        "price": 15000,
        "duration": 0,
        "type": "round",
    },
    "magnet": {
        "id": "magnet",
        "name": "Magnet",
        "icon": "🧲",
        "description": "Palavras encontradas dão +50% sats por 1 rodada.",
        "price": 8000,
        "duration": 0,
        "type": "round",
    },
    "precision": {
        "id": "precision",
        "name": "Precision",
        "icon": "🎯",
        "description": "Sem slashing por 1 rodada.",
        "price": 12000,
        "duration": 0,
        "type": "round",
    },
}

POWERUP_IDS = frozenset(POWERUP_DEFINITIONS.keys())


class PowerupActivate(BaseModel):
    """Solicitação de ativação de power-up."""
    model_config = ConfigDict(extra="forbid")

    username: Username
    powerup_id: str


async def _get_powerups(realm_id: str, username: str) -> dict[str, Any]:
    """Carrega o inventário de power-ups do jogador."""
    key = powerups_key(realm_id, username)
    raw = await redis_client.hgetall(key)
    inventory = {}
    active_timers = {}
    for field, value in raw.items():
        if field in POWERUP_IDS:
            inventory[field] = int(value)
        elif field.startswith("timer_"):
            active_timers[field] = int(value)
    # Garante que todos os power-ups apareçam no inventário
    for pid in POWERUP_IDS:
        if pid not in inventory:
            inventory[pid] = 0
    return {
        "username": username,
        "inventory": inventory,
        "active_timers": active_timers,
    }


async def _decrement_powerup(realm_id: str, username: str, powerup_id: str) -> bool:
    """Decrementa 1 unidade do power-up no inventário."""
    key = powerups_key(realm_id, username)
    current = await redis_client.hget(key, powerup_id)
    if not current or int(current) <= 0:
        return False
    await redis_client.hset(key, powerup_id, str(int(current) - 1))
    await redis_client.expire(key, 86400)
    return True


async def _activate_powerup(realm_id: str, username: str, powerup_id: str) -> dict[str, Any]:
    """Ativa um power-up: verifica inventário, decrementa, inicia timer."""
    if powerup_id not in POWERUP_DEFINITIONS:
        raise HTTPException(status_code=400, detail="Power-up inválido")
    defn = POWERUP_DEFINITIONS[powerup_id]
    # Verifica se tem no inventário
    key = powerups_key(realm_id, username)
    current = await redis_client.hget(key, powerup_id)
    if not current or int(current) <= 0:
        raise HTTPException(status_code=400, detail="Power-up não disponível no inventário")
    # Decrementa
    await redis_client.hset(key, powerup_id, str(int(current) - 1))
    # Se tem duração, inicia timer
    if defn["duration"] > 0:
        timer_field = f"timer_{powerup_id}"
        await redis_client.hset(key, timer_field, str(defn["duration"]))
        await redis_client.expire(key, defn["duration"] + 86400)
    await redis_client.expire(key, 86400)
    return {
        "status": "activated",
        "powerup_id": powerup_id,
        "name": defn["name"],
        "icon": defn["icon"],
        "duration": defn["duration"],
    }


@app.get("/api/v1/networks/{realm_id}/powerups/{username}", tags=["Power-ups"])
async def get_powerups(realm_id: str, username: str) -> dict[str, Any]:
    """Retorna o inventário de power-ups do jogador."""
    definition = get_network_definition(realm_id)
    data = await _get_powerups(definition.realm_id, username)
    # Adiciona definições completas
    data["definitions"] = [
        {
            "id": pid,
            "name": defn["name"],
            "icon": defn["icon"],
            "description": defn["description"],
            "price": defn["price"],
            "duration": defn["duration"],
            "type": defn["type"],
        }
        for pid, defn in POWERUP_DEFINITIONS.items()
    ]
    return data


@app.post("/api/v1/networks/{realm_id}/powerups/activate", tags=["Power-ups"])
async def activate_powerup(realm_id: str, data: PowerupActivate) -> dict[str, Any]:
    """Ativa um power-up do inventário do jogador."""
    definition = get_network_definition(realm_id)
    result = await _activate_powerup(definition.realm_id, data.username, data.powerup_id)
    # Retorna inventário atualizado
    inv = await _get_powerups(definition.realm_id, data.username)
    result["inventory"] = inv["inventory"]
    result["active_timers"] = inv["active_timers"]
    return result


# ==========================================================================
# Fase 9: Chat em Tempo Real — endpoint /chat/send
# ==========================================================================

# Palavras proibidas para moderação básica
CHAT_BANNED_WORDS = frozenset({
    "spam", "scam", "hack", "phish", "ban", "kill", "death",
    "hate", "abuse", "racist", "sexist", "toxic",
})

# Emojis temáticos de Bitcoin
CHAT_EMOJIS = ["🪙", "⛏️", "₿", "📡", "🔗", "⚡", "💎", "🏆"]

# Limite máximo de mensagens por minuto por jogador
CHAT_MAX_PER_MINUTE = 5
CHAT_MAX_CHARS = 100
CHAT_RATE_TTL = 60  # segundos


class ChatMessage(BaseModel):
    """Representa uma mensagem de chat enviada pelo cliente."""

    model_config = ConfigDict(extra="forbid")

    username: Username
    message: str = Field(min_length=1, max_length=CHAT_MAX_CHARS)


async def _check_chat_rate(realm_id: str, username: str) -> bool:
    """Verifica se o jogador respeita o rate limit (máx 5 msgs/minuto).

    Returns:
        ``True`` se a mensagem pode ser enviada, ``False`` se excedeu o limite.
    """
    key = chat_rate_key(realm_id, username)
    current = await redis_client.get(key)
    if current is None:
        await redis_client.set(key, "1", ex=CHAT_RATE_TTL)
        return True
    count = int(current)
    if count >= CHAT_MAX_PER_MINUTE:
        return False
    await redis_client.incr(key)
    return True


async def _is_message_banned(message: str) -> bool:
    """Verifica se a mensagem contém palavras proibidas (case-insensitive).

    Args:
        message: Texto da mensagem.

    Returns:
        ``True`` se a mensagem deve ser bloqueada.
    """
    lower = message.lower()
    for word in CHAT_BANNED_WORDS:
        if word in lower:
            return True
    return False


async def _store_chat_message(realm_id: str, username: str, message: str) -> dict[str, Any]:
    """Armazena a mensagem no Redis List e retorna o envelope pronto para broadcast.

    Mantém apenas as últimas 50 mensagens por realm.

    Args:
        realm_id: Realm de origem.
        username: Nome do jogador.
        message: Texto da mensagem.

    Returns:
        Dict com os campos da mensagem formatados para o frontend.
    """
    key = chat_messages_key(realm_id)
    envelope = {
        "action": "chat_message",
        "username": username,
        "message": message,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    # Push ao início da lista (mais recente primeiro)
    await redis_client.lpush(key, json.dumps(envelope, separators=(",", ":")))
    # Mantém apenas as últimas 50 mensagens
    await redis_client.ltrim(key, 0, 49)
    return envelope


@app.post("/api/v1/networks/{realm_id}/chat/send", tags=["Chat"])
async def send_chat_message(realm_id: str, data: ChatMessage) -> dict[str, Any]:
    """Envia uma mensagem de chat para o realm.

    Aplica moderação básica (palavras proibidas) e rate limiting
    (máx 5 mensagens por minuto por jogador).

    Args:
        realm_id: Identificador do realm.
        data: Payload com ``username`` e ``message``.

    Returns:
        Dict com ``status`` e a mensagem armazenada.

    Raises:
        HTTPException: Se a mensagem for bloqueada ou o rate limit excedido (400/429).
    """
    definition = get_network_definition(realm_id)

    # Verifica moderação
    if await _is_message_banned(data.message):
        raise HTTPException(status_code=400, detail="Mensagem contém conteúdo inadequado")

    # Verifica rate limit
    if not await _check_chat_rate(definition.realm_id, data.username):
        raise HTTPException(status_code=429, detail="Limite de mensagens excedido. Aguarde 1 minuto.")

    # Armazena e retorna
    envelope = await _store_chat_message(definition.realm_id, data.username, data.message)
    return {
        "status": "success",
        "message": envelope,
    }


@app.get("/api/v1/networks/{realm_id}/chat/history", tags=["Chat"])
async def get_chat_history(realm_id: str, limit: int = 20) -> dict[str, Any]:
    """Retorna o histórico recente de mensagens de chat.

    Args:
        realm_id: Identificador do realm.
        limit: Número máximo de mensagens (máx 50).

    Returns:
        Dict com ``realm_id`` e ``messages`` (lista ordenada do mais recente).
    """
    definition = get_network_definition(realm_id)
    key = chat_messages_key(definition.realm_id)
    raw_messages = await redis_client.lrange(key, 0, min(limit, 50) - 1)
    messages = []
    for raw in raw_messages:
        try:
            messages.append(json.loads(raw))
        except (json.JSONDecodeError, TypeError):
            continue
    return {
        "realm_id": definition.realm_id,
        "messages": messages,
    }


# ==========================================================================
# Fase 9: Mercado Player-to-Player — endpoints /market/*
# ==========================================================================

# Taxa de mercado: 5% sobre cada venda
MARKET_FEE_RATE = 0.05
# TTL para listings expirados (7 dias)
MARKET_LISTING_TTL_SECONDS = 7 * 86400
# Histórico de preços mantido (últimas 50 vendas por power-up)
MARKET_PRICE_HISTORY_LIMIT = 50


class MarketSellRequest(BaseModel):
    """Solicitação de colocação de power-up à venda no mercado."""
    model_config = ConfigDict(extra="forbid")

    username: Username
    powerup_id: str = Field(min_length=1, description="ID do power-up a ser vendido")
    price: int = Field(ge=100, le=MAX_SCORE, description="Preço em sats (mínimo 100)")


class MarketBuyRequest(BaseModel):
    """Solicitação de compra de power-up do mercado."""
    model_config = ConfigDict(extra="forbid")

    username: Username


async def _get_player_inventory(realm_id: str, username: str) -> dict[str, int]:
    """Retorna o inventário de power-ups do jogador."""
    key = powerups_key(realm_id, username)
    raw = await redis_client.hgetall(key)
    inventory: dict[str, int] = {}
    for field, value in raw.items():
        if field in POWERUP_IDS:
            inventory[field] = int(value)
    return inventory


async def _suggest_price(realm_id: str, powerup_id: str) -> int | None:
    """Calcula preço sugerido com base no histórico de vendas do power-up.

    Usa a mediana dos últimos preços de vendas. Se não há histórico,
    retorna o preço base da definição do power-up.

    Args:
        realm_id: Realm do mercado.
        powerup_id: ID do power-up.

    Returns:
        Preço sugerido em sats ou ``None`` se não há dados.
    """
    if powerup_id not in POWERUP_DEFINITIONS:
        return None

    price_key = market_price_index_key(realm_id, powerup_id)
    recent_prices = await redis_client.zrangebyscore(
        price_key, "-inf", "+inf", start=0, num=MARKET_PRICE_HISTORY_LIMIT
    )

    if not recent_prices:
        # Sem histórico — usa preço base
        return POWERUP_DEFINITIONS[powerup_id]["price"]

    prices = sorted(int(p) for p in recent_prices)
    # Retorna a mediana
    mid = len(prices) // 2
    if len(prices) % 2 == 0:
        return (prices[mid - 1] + prices[mid]) // 2
    return prices[mid]


async def _list_market(realm_id: str, *, powerup_filter: str | None = None,
                       seller_filter: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    """Lista power-ups à venda no mercado.

    Args:
        realm_id: Realm do mercado.
        powerup_filter: Se fornecido, filtra por tipo de power-up.
        seller_filter: Se fornecido, filtra por vendedor.
        limit: Número máximo de resultados.

    Returns:
        Lista de listings ordenados por preço (mais barato primeiro).
    """
    key = market_list_key(realm_id)
    # Obtém todos os listings ordenados por preço
    if limit <= 0:
        return []
    raw_listings = await redis_client.zrange(key, 0, limit - 1, withscores=True)

    listings = []
    for member_str, score in raw_listings:
        try:
            listing = json.loads(member_str)
        except (json.JSONDecodeError, TypeError):
            continue

        # Aplica filtros
        if powerup_filter and listing.get("powerup_id") != powerup_filter:
            continue
        if seller_filter and listing.get("seller") != seller_filter:
            continue

        listing["price"] = int(score)
        listing["price_formatted"] = f"{int(score):,}"
        listings.append(listing)

    return listings


async def _record_sale_price(realm_id: str, powerup_id: str, price: int) -> None:
    """Registra um preço de venda no índice de preços para cálculo de sugestão."""
    price_key = market_price_index_key(realm_id, powerup_id)
    timestamp = datetime.datetime.now(datetime.timezone.utc).timestamp()
    await redis_client.zadd(price_key, {str(price): timestamp})
    # Mantém apenas os últimos N preços
    await redis_client.zremrangebyrank(price_key, 0, -MARKET_PRICE_HISTORY_LIMIT - 1)


@app.get("/api/v1/networks/{realm_id}/market/list", tags=["Mercado"])
async def get_market_list(
    realm_id: str,
    powerup: str | None = None,
    seller: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Lista power-ups à venda no mercado player-to-player.

    Os listings são ordenados por preço (mais barato primeiro).
    Filtros opcionais por tipo de power-up e vendedor.

    Args:
        realm_id: Identificador do realm.
        powerup: Filtro por tipo de power-up (ex: "scanner").
        seller: Filtro por nome do vendedor.
        limit: Número máximo de resultados.

    Returns:
        Dict com ``realm_id``, ``listings`` e ``suggested_prices``.
    """
    definition = get_network_definition(realm_id)
    listings = await _list_market(
        definition.realm_id,
        powerup_filter=powerup,
        seller_filter=seller,
        limit=limit,
    )

    # Calcula preços sugeridos para cada power-up listado
    suggested_prices: dict[str, int | None] = {}
    for listing in listings:
        pid = listing["powerup_id"]
        if pid not in suggested_prices:
            suggested_prices[pid] = await _suggest_price(definition.realm_id, pid)

    return {
        "realm_id": definition.realm_id,
        "listings": listings,
        "suggested_prices": suggested_prices,
        "total": len(listings),
    }


@app.post("/api/v1/networks/{realm_id}/market/sell", tags=["Mercado"])
async def sell_on_market(realm_id: str, data: MarketSellRequest) -> dict[str, Any]:
    """Coloca um power-up do inventário do jogador à venda no mercado.

    O power-up é removido do inventário do vendedor e adicionado ao
    Sorted Set do mercado ordenado por preço. Taxa de 5% não se aplica
    aqui — a taxa é cobrada na compra.

    Args:
        realm_id: Identificador do realm.
        data: Payload com ``username``, ``powerup_id`` e ``price``.

    Returns:
        Dict com ``status`` e detalhes do listing.

    Raises:
        HTTPException: Se o power-up não existe, o jogador não tem no inventário,
                       ou o preço é inválido (400).
    """
    definition = get_network_definition(realm_id)
    realm = definition.realm_id

    # Valida o power-up
    if data.powerup_id not in POWERUP_DEFINITIONS:
        raise HTTPException(status_code=400, detail="Power-up inválido")

    # Prepara o listing antes da operação atômica no Redis.
    inventory_key = powerups_key(realm, data.username)
    market_key = market_list_key(realm)
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    listing_data = {
        "seller": data.username,
        "powerup_id": data.powerup_id,
        "powerup_name": POWERUP_DEFINITIONS[data.powerup_id]["name"],
        "powerup_icon": POWERUP_DEFINITIONS[data.powerup_id]["icon"],
        "price": data.price,
        "timestamp": timestamp.isoformat(),
    }
    member_str = json.dumps(listing_data, separators=(",", ":"))

    lua_script = """
    local inventory_key = KEYS[1]
    local market_key = KEYS[2]
    local powerup_id = ARGV[1]
    local member = ARGV[2]
    local price = tonumber(ARGV[3])
    local listing_ttl = tonumber(ARGV[4])

    local inventory_type = redis.call('type', inventory_key)['ok']
    local market_type = redis.call('type', market_key)['ok']
    if inventory_type ~= 'none' and inventory_type ~= 'hash' then
        return 'invalid_storage_type'
    end
    if market_type ~= 'none' and market_type ~= 'zset' then
        return 'invalid_storage_type'
    end

    local available = tonumber(redis.call('hget', inventory_key, powerup_id) or '0')
    if available <= 0 then
        return 'inventory_empty'
    end

    redis.call('hincrby', inventory_key, powerup_id, -1)
    redis.call('expire', inventory_key, 86400)
    redis.call('zadd', market_key, price, member)
    redis.call('expire', market_key, listing_ttl)
    return 'ok'
    """
    eval_result = await redis_client.eval(
        lua_script,
        2,
        inventory_key,
        market_key,
        data.powerup_id,
        member_str,
        str(data.price),
        str(MARKET_LISTING_TTL_SECONDS),
    )
    status = eval_result.decode() if isinstance(eval_result, bytes) else str(eval_result)
    if status == "inventory_empty":
        raise HTTPException(status_code=400, detail="Power-up não disponível no inventário")
    if status == "invalid_storage_type":
        raise HTTPException(status_code=500, detail="Estrutura interna do mercado inválida")
    if status != "ok":
        raise HTTPException(status_code=500, detail="Falha inesperada ao publicar listing")

    logger.info(
        "Power-up listado no mercado: %s por %d sats (vendedor: %s, realm: %s)",
        data.powerup_id, data.price, data.username, realm,
    )

    return {
        "status": "listed",
        "listing": listing_data,
    }


@app.post("/api/v1/networks/{realm_id}/market/buy", tags=["Mercado"])
async def buy_from_market(realm_id: str, data: MarketBuyRequest) -> dict[str, Any]:
    """Compra um power-up do mercado player-to-player.

    O comprador paga o preço + taxa de 5%. O power-up é transferido
    do vendedor para o comprador. O vendedor recebe o valor menos a taxa.

    Args:
        realm_id: Identificador do realm.
        data: Payload com ``username`` (comprador).

    Returns:
        Dict com ``status``, ``powerup`` comprado e ``seller_earnings``.

    Raises:
        HTTPException: Se o mercado está vazio, o jogador não tem saldo
                       suficiente, ou o listing foi removido (400/402/404).
    """
    definition = get_network_definition(realm_id)
    realm = definition.realm_id
    buyer = data.username

    # Obtém o listing mais barato (primeiro do Sorted Set)
    market_key = market_list_key(realm)
    result = await redis_client.zpopmin(market_key, 1)

    if not result:
        raise HTTPException(status_code=404, detail="Mercado vazio — nenhum power-up à venda")

    member_str, price = result[0]

    try:
        listing = json.loads(member_str)
    except (json.JSONDecodeError, TypeError):
        # Listing corrompido — remove e tenta o próximo
        raise HTTPException(status_code=500, detail="Listing corrompido — tente novamente")

    seller = listing["seller"]
    powerup_id = listing["powerup_id"]

    if powerup_id not in POWERUP_DEFINITIONS:
        raise HTTPException(status_code=400, detail="Power-up inválido no listing")

    # Calcula preços com taxa de 5%
    fee_amount = int(price * MARKET_FEE_RATE)
    total_cost = price + fee_amount
    seller_earnings = price - fee_amount

    state_key = player_state_key(realm, buyer)

    # Transação atômica via script Lua
    lua_script = """
    local buyer_key = KEYS[1]
    local seller_key = KEYS[2]
    local powerups_buyer = KEYS[3]
    local history_key = KEYS[4]
    local price_key = KEYS[5]

    local buyer_type = redis.call('type', buyer_key)['ok']
    local seller_type = redis.call('type', seller_key)['ok']
    local inventory_type = redis.call('type', powerups_buyer)['ok']
    local history_type = redis.call('type', history_key)['ok']
    local price_type = redis.call('type', price_key)['ok']
    if (buyer_type ~= 'none' and buyer_type ~= 'hash')
        or (seller_type ~= 'none' and seller_type ~= 'hash')
        or (inventory_type ~= 'none' and inventory_type ~= 'hash')
        or (history_type ~= 'none' and history_type ~= 'zset')
        or (price_type ~= 'none' and price_type ~= 'zset') then
        return 'invalid_storage_type'
    end

    -- Debita do comprador
    local buyer_bal = tonumber(redis.call('hget', buyer_key, 'balance') or '0')
    if buyer_bal < tonumber(ARGV[1]) then
        return 'buyer_insufficient'
    end
    redis.call('hincrby', buyer_key, 'balance', -tonumber(ARGV[1]))

    -- Credita ao vendedor (menos taxa)
    redis.call('hincrby', seller_key, 'balance', tonumber(ARGV[2]))

    -- O item já saiu do vendedor ao ser colocado em escrow no listing.
    redis.call('hincrby', powerups_buyer, ARGV[3], 1)

    -- Registra no histórico de vendas
    redis.call('zadd', history_key, ARGV[4], ARGV[5])

    -- Registra preço no índice
    redis.call('zadd', price_key, ARGV[6], ARGV[4])

    return 'ok'
    """

    timestamp = datetime.datetime.now(datetime.timezone.utc).timestamp()
    listing_json = json.dumps(listing, separators=(",", ":"))
    history_key = market_history_key(realm)

    eval_result = await redis_client.eval(
        lua_script,
        5,
        state_key,
        player_state_key(realm, seller),
        powerups_key(realm, buyer),
        history_key,
        market_price_index_key(realm, powerup_id),
        str(total_cost),
        str(seller_earnings),
        powerup_id,
        str(timestamp),
        listing_json,
        str(price),
    )

    status = eval_result.decode() if isinstance(eval_result, bytes) else str(eval_result)
    if status == "buyer_insufficient":
        await redis_client.zadd(market_key, {member_str: price})
        raise HTTPException(
            status_code=402,
            detail=f"Saldo insuficiente. Custo total: {total_cost:,} sats (preço: {price:,} + taxa: {fee_amount:,})",
            headers={"Retry-After": "1"},
        )
    if status != "ok":
        await redis_client.zadd(market_key, {member_str: price})
        detail = (
            "Estrutura interna do mercado inválida"
            if status == "invalid_storage_type"
            else "Falha inesperada na transferência do mercado"
        )
        raise HTTPException(status_code=500, detail=detail)

    # Atualiza UI do vendedor (se online)
    logger.info(
        "Power-up vendido no mercado: %s por %d sats (comprador: %s, vendedor: %s, taxa: %d sats, realm: %s)",
        powerup_id, price, buyer, seller, fee_amount, realm,
    )

    powerup_def = POWERUP_DEFINITIONS[powerup_id]

    return {
        "status": "purchased",
        "powerup": {
            "id": powerup_id,
            "name": powerup_def["name"],
            "icon": powerup_def["icon"],
            "description": powerup_def["description"],
        },
        "price": price,
        "fee": fee_amount,
        "total_cost": total_cost,
        "seller_earnings": seller_earnings,
        "buyer": buyer,
        "seller": seller,
    }


@app.get("/api/v1/networks/{realm_id}/market/history", tags=["Mercado"])
async def get_market_history(realm_id: str, limit: int = 30) -> dict[str, Any]:
    """Retorna o histórico recente de vendas do mercado.

    Args:
        realm_id: Identificador do realm.
        limit: Número máximo de vendas retornadas.

    Returns:
        Dict com ``realm_id`` e ``sales`` (lista ordenada da mais recente).
    """
    definition = get_network_definition(realm_id)
    key = market_history_key(definition.realm_id)

    # ZREVRANGE para obter do mais recente
    raw_sales = await redis_client.zrevrange(key, 0, limit - 1)

    sales = []
    for member_str in raw_sales:
        try:
            sale = json.loads(member_str)
            sale["price"] = int(sale.get("price", 0))
            sales.append(sale)
        except (json.JSONDecodeError, TypeError):
            continue

    return {
        "realm_id": definition.realm_id,
        "sales": sales,
        "total": len(sales),
    }


# ==========================================================================
# Fase 9: Desafios PvP (Head-to-Head) — endpoints /pvp/*
# ==========================================================================

# Duração padrão de um desafio PvP (segundos)
PVP_DURATION = 60
# Taxa de transferência do perdedor para o vencedor (%)
PVP_TRANSFER_RATE = 0.10
# Diferença máxima de nível para matchmaking
PVP_LEVEL_DIFF_MAX = 10
# Número de palavras por partida PvP
PVP_WORDS_PER_MATCH = 6


class PvpChallengeRequest(BaseModel):
    """Solicitação de desafio PvP."""
    model_config = ConfigDict(extra="forbid")

    username: Username
    target_username: Username = Field(
        alias="target",
        description="Nome do jogador desafiado",
    )


class PvpAcceptRequest(BaseModel):
    """Solicitação de aceite de desafio PvP."""
    model_config = ConfigDict(extra="forbid")

    username: Username


class PvpScoreUpdate(BaseModel):
    """Atualização de pontuação durante um desafio PvP."""
    model_config = ConfigDict(extra="forbid")

    username: Username
    score: int = Field(ge=0, le=MAX_SCORE)


def _normalize_pvp_pair(challenger: str, challenged: str) -> tuple[str, str]:
    """Retorna (nome_alfabeticamente_primeiro, nome_segundo) para unicidade."""
    a, b = sorted([challenger, challenged])
    return a, b


async def _get_pvp_match(realm_id: str, challenger: str, challenged: str) -> dict[str, Any] | None:
    """Carrega o estado de um desafio PvP do Redis."""
    key = pvp_match_key(realm_id, challenger, challenged)
    raw = await redis_client.hgetall(key)
    if not raw:
        return None
    return {
        "challenger": raw.get("challenger", ""),
        "challenged": raw.get("challenged", ""),
        "state": raw.get("state", "pending"),
        "realm_id": raw.get("realm_id", ""),
        "words": json.loads(raw.get("words", "[]")),
        "grid_size": int(raw.get("grid_size", 12)),
        "challenger_score": int(raw.get("challenger_score", 0)),
        "challenged_score": int(raw.get("challenged_score", 0)),
        "challenger_found": int(raw.get("challenger_found", 0)),
        "challenged_found": int(raw.get("challenged_found", 0)),
        "timer": int(raw.get("timer", PVP_DURATION)),
        "started_at": raw.get("started_at", ""),
        "ended_at": raw.get("ended_at", ""),
        "winner": raw.get("winner", ""),
        "loser": raw.get("loser", ""),
        "transfer_amount": int(raw.get("transfer_amount", 0)),
    }


async def _publish_pvp_event(realm_id: str, event: dict[str, Any]) -> None:
    """Publica um evento PvP no canal PubSub para broadcast WebSocket."""
    channel = pvp_active_channel(realm_id)
    await redis_client.publish(channel, json.dumps(event, separators=(",", ":")))


async def _create_pvp_match(
    realm_id: str,
    challenger: str,
    challenged: str,
    words: list[str],
    grid_size: int,
) -> dict[str, Any]:
    """Cria um novo desafio PvP no Redis."""
    key = pvp_match_key(realm_id, challenger, challenged)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    match_data = {
        "challenger": challenger,
        "challenged": challenged,
        "state": "pending",
        "realm_id": realm_id,
        "words": json.dumps(words),
        "grid_size": str(grid_size),
        "challenger_score": "0",
        "challenged_score": "0",
        "challenger_found": "0",
        "challenged_found": "0",
        "timer": str(PVP_DURATION),
        "started_at": "",
        "ended_at": "",
        "winner": "",
        "loser": "",
        "transfer_amount": "0",
    }

    await redis_client.hset(key, mapping=match_data)
    await redis_client.expire(key, 86400)  # 24h TTL

    return await _get_pvp_match(realm_id, challenger, challenged)


async def _start_pvp_match(realm_id: str, challenger: str, challenged: str) -> dict[str, Any]:
    """Inicia um desafio PvP (muda estado para 'in_progress')."""
    key = pvp_match_key(realm_id, challenger, challenged)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    await redis_client.hset(key, "state", "in_progress")
    await redis_client.hset(key, "started_at", now)
    await redis_client.hset(key, "timer", str(PVP_DURATION))

    match = await _get_pvp_match(realm_id, challenger, challenged)

    # Publica evento de início
    await _publish_pvp_event(realm_id, {
        "action": "pvp_start",
        "realm_id": realm_id,
        "challenger": challenger,
        "challenged": challenged,
        "words": json.loads(match["words"]),
        "grid_size": match["grid_size"],
        "duration": PVP_DURATION,
        "started_at": now,
    })

    return match


async def _update_pvp_score(
    realm_id: str,
    username: str,
    score: int,
    found_count: int,
) -> dict[str, Any]:
    """Atualiza a pontuação de um jogador durante um PvP."""
    # Encontra o match ativo do jogador
    # Usa um padrão de busca — o match key é pvp:{a}:{b}
    # Precisamos encontrar qual match este jogador participa
    pattern = f"{PREFIX}:*:pvp:*"
    cursor = 0
    match_key = None
    match_data = None

    while True:
        cursor, keys = await redis_client.scan(cursor, match=pattern, count=100)
        for key in keys:
            state = await redis_client.hget(key, "state")
            if state != "in_progress":
                continue
            challenger = await redis_client.hget(key, "challenger")
            challenged = await redis_client.hget(key, "challenged")
            if username not in (challenger, challenged):
                continue

            match_key = key
            raw = await redis_client.hgetall(key)
            match_data = {
                "challenger": raw.get("challenger", ""),
                "challenged": raw.get("challenged", ""),
                "state": raw.get("state", ""),
                "realm_id": raw.get("realm_id", ""),
                "words": json.loads(raw.get("words", "[]")),
                "grid_size": int(raw.get("grid_size", 12)),
                "challenger_score": int(raw.get("challenger_score", 0)),
                "challenged_score": int(raw.get("challenged_score", 0)),
                "challenger_found": int(raw.get("challenger_found", 0)),
                "challenged_found": int(raw.get("challenged_found", 0)),
                "timer": int(raw.get("timer", PVP_DURATION)),
                "started_at": raw.get("started_at", ""),
                "ended_at": raw.get("ended_at", ""),
                "winner": raw.get("winner", ""),
                "loser": raw.get("loser", ""),
                "transfer_amount": int(raw.get("transfer_amount", 0)),
            }
            break

        if cursor == 0:
            break

    if not match_key or not match_data:
        raise HTTPException(status_code=404, detail="Desafio PvP não encontrado ou não em andamento")

    realm = match_data["realm_id"]
    challenger = match_data["challenger"]
    challenged = match_data["challenged"]

    # Determina se é challenger ou challenged
    is_challenger = username == challenger
    score_field = "challenger_score" if is_challenger else "challenged_score"
    found_field = "challenger_found" if is_challenger else "challenged_found"

    await redis_client.hset(match_key, score_field, str(score))
    await redis_client.hset(match_key, found_field, str(found_count))

    updated = await _get_pvp_match(realm, challenger, challenged)

    # Publica evento de score
    await _publish_pvp_event(realm, {
        "action": "pvp_score_update",
        "realm_id": realm,
        "challenger": challenger,
        "challenged": challenged,
        "username": username,
        "score": score,
        "found": found_count,
    })

    return updated


async def _end_pvp_match(
    realm_id: str,
    challenger: str,
    challenged: str,
    winner: str,
    loser: str,
) -> dict[str, Any]:
    """Finaliza um desafio PvP e transfere saldo."""
    key = pvp_match_key(realm_id, challenger, challenged)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Obtém dados atuais
    raw = await redis_client.hgetall(key)
    challenger_score = int(raw.get("challenger_score", 0))
    challenged_score = int(raw.get("challenged_score", 0))

    # Determina vencedor por pontuação
    if challenger_score > challenged_score:
        winner, loser = challenger, challenged
    elif challenged_score > challenger_score:
        winner, loser = challenged, challenger
    else:
        # Empate — sem transferência
        await redis_client.hset(key, "state", "draw")
        await redis_client.hset(key, "ended_at", now)
        await redis_client.hset(key, "winner", "")
        await redis_client.hset(key, "loser", "")
        await redis_client.hset(key, "transfer_amount", "0")

        await _publish_pvp_event(realm_id, {
            "action": "pvp_end",
            "realm_id": realm_id,
            "challenger": challenger,
            "challenged": challenged,
            "result": "draw",
            "challenger_score": challenger_score,
            "challenged_score": challenged_score,
            "ended_at": now,
        })

        return await _get_pvp_match(realm_id, challenger, challenged)

    # Calcula transferência (10% do saldo do perdedor, mínimo 0)
    loser_state_key = player_state_key(realm_id, loser)
    loser_balance_raw = await redis_client.hget(loser_state_key, "balance")
    loser_balance = int(loser_balance_raw) if loser_balance_raw else 0
    transfer_amount = max(0, int(loser_balance * PVP_TRANSFER_RATE))

    # Transfere saldo (garante que perdedor não fica negativo)
    winner_state_key = player_state_key(realm_id, winner)
    if transfer_amount > 0:
        await redis_client.hincrby(loser_state_key, "balance", -transfer_amount)
        await redis_client.hincrby(winner_state_key, "balance", transfer_amount)

    # Atualiza estado do match
    await redis_client.hset(key, "state", "finished")
    await redis_client.hset(key, "ended_at", now)
    await redis_client.hset(key, "winner", winner)
    await redis_client.hset(key, "loser", loser)
    await redis_client.hset(key, "transfer_amount", str(transfer_amount))

    await _publish_pvp_event(realm_id, {
        "action": "pvp_end",
        "realm_id": realm_id,
        "challenger": challenger,
        "challenged": challenged,
        "result": "win",
        "winner": winner,
        "loser": loser,
        "challenger_score": challenger_score,
        "challenged_score": challenged_score,
        "transfer_amount": transfer_amount,
        "ended_at": now,
    })

    return await _get_pvp_match(realm_id, challenger, challenged)


# Endpoint: GET /pvp/match/{challenger}/{challenged} — consulta estado de um desafio
@app.get("/api/v1/networks/{realm_id}/pvp/match/{challenger}/{challenged}", tags=["PvP"])
async def get_pvp_match_endpoint(realm_id: str, challenger: str, challenged: str) -> dict[str, Any]:
    """Retorna o estado atual de um desafio PvP.

    Args:
        realm_id: Identificador do realm.
        challenger: Nome do desafiante.
        challenged: Nome do desafiado.

    Returns:
        Dict com o estado do desafio ou 404 se não existir.
    """
    definition = get_network_definition(realm_id)
    match = await _get_pvp_match(definition.realm_id, challenger, challenged)
    if not match:
        raise HTTPException(status_code=404, detail="Desafio PvP não encontrado")
    return match


# Endpoint: POST /pvp/challenge — enviar desafio
@app.post("/api/v1/networks/{realm_id}/pvp/challenge", tags=["PvP"])
async def challenge_player(realm_id: str, data: PvpChallengeRequest) -> dict[str, Any]:
    """Envia um desafio PvP para outro jogador.

    Realiza matchmaking por nível próximo (diferença máx 10 níveis).
    Gera 6 palavras aleatórias para ambos os jogadores.

    Args:
        realm_id: Identificador do realm.
        data: Payload com ``username`` (desafiante) e ``target`` (desafiado).

    Returns:
        Dict com ``status`` e dados do desafio criado.

    Raises:
        HTTPException: Se o jogador alvo não existe, nível incompatível,
                       ou desafio já existe (400/404).
    """
    definition = get_network_definition(realm_id)
    realm = definition.realm_id
    challenger = data.username
    target = data.target

    # Não pode desafiar a si mesmo
    if challenger == target:
        raise HTTPException(status_code=400, detail="Não é possível desafiar a si mesmo")

    # Verifica se o jogador alvo existe no leaderboard
    leaderboard = await redis_client.zrevrange(leaderboard_key(realm), 0, -1, withscores=True)
    leaderboard_dict = {u: s for u, s in leaderboard}
    if target not in leaderboard_dict:
        raise HTTPException(status_code=404, detail="Jogador alvo não encontrado no ranking")

    # Verifica se já existe um desafio ativo
    existing = await _get_pvp_match(realm, challenger, target)
    if existing and existing["state"] in ("pending", "in_progress"):
        raise HTTPException(status_code=400, detail="Já existe um desafio ativo entre estes jogadores")

    # Verifica matchmaking por nível — obtém níveis de ambos
    challenger_level_key = level_key(realm, challenger)
    target_level_key = level_key(realm, target)

    challenger_level_raw = await redis_client.hget(challenger_level_key, "level")
    target_level_raw = await redis_client.hget(target_level_key, "level")

    challenger_level = int(challenger_level_raw) if challenger_level_raw else 1
    target_level = int(target_level_raw) if target_level_raw else 1

    if abs(challenger_level - target_level) > PVP_LEVEL_DIFF_MAX:
        raise HTTPException(
            status_code=400,
            detail=f"Diferença de nível muito grande ({abs(challenger_level - target_level)} > {PVP_LEVEL_DIFF_MAX})",
        )

    # Gera 6 palavras aleatórias para o match
    import random
    word_pool = [
        "BLOCK", "HASH", "NODE", "CHAIN", "MINE", "FORK",
        "WALLET", "KEY", "SEED", "TX", "POOL", "DIFF",
        "NONCE", "MERKLE", "SIG", "P2P", "UTXO", "DUST",
        "FEE", "MEME", "ORPHAN", "STAKE", "LIGHT", "SIGH",
    ]
    random.shuffle(word_pool)
    match_words = word_pool[:PVP_WORDS_PER_MATCH]

    # Determina grid size baseado nos níveis
    avg_level = (challenger_level + target_level) / 2
    if avg_level >= 3:
        grid_size = 15
    elif avg_level >= 2:
        grid_size = 12
    else:
        grid_size = 10

    # Cria o match
    match = await _create_pvp_match(realm, challenger, target, match_words, grid_size)

    # Publica evento de desafio
    await _publish_pvp_event(realm, {
        "action": "pvp_challenge",
        "realm_id": realm,
        "challenger": challenger,
        "challenged": target,
        "challenger_level": challenger_level,
        "challenged_level": target_level,
        "words": match_words,
        "grid_size": grid_size,
        "transfer_rate": PVP_TRANSFER_RATE,
    })

    return {
        "status": "challenge_sent",
        "match": match,
    }


# Endpoint: POST /pvp/accept — aceitar desafio
@app.post("/api/v1/networks/{realm_id}/pvp/accept", tags=["PvP"])
async def accept_challenge(realm_id: str, data: PvpAcceptRequest) -> dict[str, Any]:
    """Aceita um desafio PvP recebido.

    Args:
        realm_id: Identificador do realm.
        data: Payload com ``username`` (jogador que aceita).

    Returns:
        Dict com ``status`` e dados do match iniciado.

    Raises:
        HTTPException: Se o jogador não foi desafiado,
                       ou o desafio não existe (400/404).
    """
    definition = get_network_definition(realm_id)
    realm = definition.realm_id
    acceptor = data.username

    # Encontra o match onde este jogador é o desafiado
    pattern = f"{PREFIX}:*:pvp:*"
    cursor = 0
    match_key = None

    while True:
        cursor, keys = await redis_client.scan(cursor, match=pattern, count=100)
        for key in keys:
            state = await redis_client.hget(key, "state")
            if state != "pending":
                continue
            challenged = await redis_client.hget(key, "challenged")
            if challenged == acceptor:
                match_key = key
                break
        if cursor == 0:
            break

    if not match_key:
        raise HTTPException(status_code=404, detail="Desafio pendente não encontrado para este jogador")

    raw = await redis_client.hgetall(match_key)
    challenger = raw.get("challenger", "")
    challenged = raw.get("challenged", "")

    if challenged != acceptor:
        raise HTTPException(status_code=400, detail="Você não é o desafiado neste match")

    # Inicia o match
    match = await _start_pvp_match(realm, challenger, challenged)

    return {
        "status": "match_started",
        "match": match,
    }


# Endpoint: POST /pvp/score — enviar pontuação durante PvP
@app.post("/api/v1/networks/{realm_id}/pvp/score", tags=["PvP"])
async def submit_pvp_score(realm_id: str, data: PvpScoreUpdate) -> dict[str, Any]:
    """Envia a pontuação atual durante um desafio PvP.

    Args:
        realm_id: Identificador do realm.
        data: Payload com ``username`` e ``score``.

    Returns:
        Dict com o estado atualizado do match.
    """
    definition = get_network_definition(realm_id)
    updated = await _update_pvp_score(
        definition.realm_id,
        data.username,
        data.score,
        data.score // 100,  # found_count estimado baseado na score
    )
    return {"status": "score_updated", "match": updated}


# ==========================================================================
# Fase 9: Desafios PvP — eventos WebSocket
# ==========================================================================

# Adiciona ações PvP ao conjunto de eventos públicos
PUBLIC_EVENT_FIELDS["pvp_challenge"] = frozenset({
    "challenger", "challenged", "challenger_level", "challenged_level",
    "words", "grid_size", "transfer_rate",
})
PUBLIC_EVENT_FIELDS["pvp_start"] = frozenset({
    "challenger", "challenged", "words", "grid_size",
    "duration", "started_at",
})
PUBLIC_EVENT_FIELDS["pvp_score_update"] = frozenset({
    "challenger", "challenged", "username", "score", "found",
})
PUBLIC_EVENT_FIELDS["pvp_end"] = frozenset({
    "challenger", "challenged", "result", "winner", "loser",
    "challenger_score", "challenged_score", "transfer_amount", "ended_at",
})
PUBLIC_EVENT_FIELDS["pvp_timer"] = frozenset({
    "challenger", "challenged", "timer",
})


# ==========================================================================
# Fase 9: Tokens Colecionáveis (Block Cards) — endpoint /cards
# ==========================================================================

# Definições de raridade dos cards
CARD_RARITIES = {
    "common": {
        "name": "Common",
        "icon": "⛏️",
        "color": "#94a3b8",
        "border": "rgba(148, 163, 184, 0.4)",
        "bg": "rgba(148, 163, 184, 0.08)",
        "weight": 60,
    },
    "rare": {
        "name": "Rare",
        "icon": "💎",
        "color": "#a855f7",
        "border": "rgba(168, 85, 247, 0.5)",
        "bg": "rgba(168, 85, 247, 0.1)",
        "weight": 25,
    },
    "epic": {
        "name": "Epic",
        "icon": "🔥",
        "color": "#f97316",
        "border": "rgba(249, 115, 22, 0.5)",
        "bg": "rgba(249, 115, 22, 0.1)",
        "weight": 10,
    },
    "legendary": {
        "name": "Legendary",
        "icon": "🌟",
        "color": "#eab308",
        "border": "rgba(234, 179, 8, 0.6)",
        "bg": "rgba(234, 179, 8, 0.12)",
        "weight": 5,
    },
}

# Bônus de coleção completa por raridade
COLLECTION_BONUSES = {
    "common": {"count": 10, "bonus": {"type": "reward_percent", "value": 0.01}},
    "rare": {"count": 5, "bonus": {"type": "reward_percent", "value": 0.02}},
    "epic": {"count": 3, "bonus": {"type": "reward_percent", "value": 0.03}},
    "legendary": {"count": 1, "bonus": {"type": "reward_percent", "value": 0.05}},
}


async def _get_player_cards(realm_id: str, username: str) -> dict[str, Any]:
    """Retorna a coleção de cards do jogador.

    Lê do Redis Set (cards_set_key) e depois busca os detalhes de cada card.

    Args:
        realm_id: Identificador do realm.
        username: Nome do minerador.

    Returns:
        Dict com ``cards`` (lista de cards), ``total``, ``by_rarity`` e ``collection_bonus``.
    """
    cards_key = cards_set_key(realm_id, username)
    block_hashes = await redis_client.smembers(cards_key)

    cards = []
    by_rarity = {"common": 0, "rare": 0, "epic": 0, "legendary": 0}

    for bh in sorted(block_hashes, reverse=True):
        detail_key = card_detail_key(realm_id, username, bh)
        raw = await redis_client.hgetall(detail_key)
        if not raw:
            # Tenta buscar do card global (gerado pelo ingestor)
            global_key = card_detail_key(realm_id, "global", bh)
            raw = await redis_client.hgetall(global_key)
        if not raw:
            continue

        rarity = raw.get("rarity", "common")
        by_rarity[rarity] = by_rarity.get(rarity, 0) + 1

        cards.append({
            "block_hash": raw.get("block_hash", bh),
            "rarity": rarity,
            "rarity_info": CARD_RARITIES.get(rarity, CARD_RARITIES["common"]),
            "mempool_count": int(raw.get("mempool_count", 0)),
            "discarded_backlog": int(raw.get("discarded_backlog", 0)),
            "block_number": int(raw.get("block_number", 0)),
            "is_halving": raw.get("is_halving", "false") == "true",
            "timestamp": raw.get("timestamp", ""),
        })

    # Calcula bônus de coleção
    collection_bonus = {}
    for rarity, bonus_def in COLLECTION_BONUSES.items():
        count = by_rarity.get(rarity, 0)
        collection_bonus[rarity] = {
            "owned": count,
            "required": bonus_def["count"],
            "complete": count >= bonus_def["count"],
            "bonus": bonus_def["bonus"],
        }

    return {
        "realm_id": realm_id,
        "username": username,
        "cards": cards,
        "total": len(cards),
        "by_rarity": by_rarity,
        "collection_bonus": collection_bonus,
    }


@app.get("/api/v1/networks/{realm_id}/cards/{username}", tags=["Cards"])
async def get_player_cards(realm_id: str, username: str) -> dict[str, Any]:
    """Retorna a coleção de Block Cards do jogador.

    Args:
        realm_id: Identificador do realm.
        username: Nome do minerador.

    Returns:
        Dict com ``realm_id``, ``username``, ``cards`` (lista), ``total``,
        ``by_rarity`` (contagem por raridade) e ``collection_bonus``.
    """
    definition = get_network_definition(realm_id)
    return await _get_player_cards(definition.realm_id, username)


# ==========================================================================
# Fase 10: Mempool Crates — loot boxes
# ==========================================================================

# Tabela de drop das crates
CRATE_PRICES = {"crate": 5000}  # preço em sats
CRATE_FREE_INTERVAL = 10  # blocos entre crates grátis

# Power-ups disponíveis como drop
CRATE_POWERUPS = [
    {"id": "speed_boost", "name": "Speed Boost", "icon": "⚡", "description": "Reduz tempo de cooldown em 20%"},
    {"id": "golden_eye", "name": "Golden Eye", "icon": "👁️", "description": "Próxima palavra golden garantida"},
    {"id": "combo_lock", "name": "Combo Lock", "icon": "🔒", "description": "Trava combo 2× por 3 blocos"},
    {"id": "extra_time", "name": "Extra Time", "icon": "⏱️", "description": "+15s no próximo bloco"},
    {"id": "double_sats", "name": "Double Sats", "icon": "💰", "description": "Recompensa 2× no próximo bloco"},
]

# Skins exclusivas
CRATE_SKINS = [
    {"id": "skin_neon", "name": "Neon Grid", "icon": "🌈", "description": "Grade com bordas neon"},
    {"id": "skin_retro", "name": "Retro Terminal", "icon": "📟", "description": "Visual de terminal verde"},
    {"id": "skin_golden", "name": "Golden Hash", "icon": "✨", "description": "Grade dourada"},
    {"id": "skin_dark", "name": "Dark Matter", "icon": "🌑", "description": "Grade ultra-escura"},
]

# Itens legendários
CRATE_LEGENDARY = [
    {"id": "legendary_halving_boost", "name": "Halving Boost", "icon": "🏆", "description": "Bônus permanente +5% em recompensas"},
    {"id": "legendary_mempool_lord", "name": "Mempool Lord", "icon": "👑", "description": "Bônus permanente +5% em recompensas"},
]


def _roll_crate_item() -> dict[str, Any]:
    """Determina o item dropado pela crate usando rolagem ponderada.

    Probabilidades:
        60%: sats (1.000-10.000)
        20%: power-up aleatório
        12%: block card raro
        6%: skin exclusiva
        2%: item legendário (+5% bônus permanente)

    Returns:
        Dict com ``type``, ``rarity``, ``name``, ``icon``, ``description`` e
        opcionalmente ``value`` (para sats) ou ``permanent_bonus`` (para legendário).
    """
    roll = random.random() * 100  # 0-100

    if roll < 60:
        # 60% — sats
        value = random.randint(1000, 10000)
        return {
            "type": "sats",
            "rarity": "common",
            "name": f"{value:,} sats",
            "icon": "🪙",
            "description": f"Recebeu {value:,} sats da crate!",
            "value": value,
        }
    elif roll < 80:
        # 20% — power-up
        powerup = random.choice(CRATE_POWERUPS)
        return {
            "type": "powerup",
            "rarity": "uncommon",
            "name": powerup["name"],
            "icon": powerup["icon"],
            "description": powerup["description"],
            "powerup_id": powerup["id"],
        }
    elif roll < 92:
        # 12% — block card raro
        card_rarity = random.choice(["rare", "epic"])
        rarity_info = CARD_RARITIES.get(card_rarity, CARD_RARITIES["rare"])
        return {
            "type": "block_card",
            "rarity": card_rarity,
            "name": f"Block Card {rarity_info['name']}",
            "icon": rarity_info["icon"],
            "description": f"Block Card {rarity_info['name']} adicionado à coleção!",
        }
    elif roll < 98:
        # 6% — skin exclusiva
        skin = random.choice(CRATE_SKINS)
        return {
            "type": "skin",
            "rarity": "rare",
            "name": skin["name"],
            "icon": skin["icon"],
            "description": skin["description"],
            "skin_id": skin["id"],
        }
    else:
        # 2% — item legendário
        legendary = random.choice(CRATE_LEGENDARY)
        return {
            "type": "legendary",
            "rarity": "legendary",
            "name": legendary["name"],
            "icon": legendary["icon"],
            "description": legendary["description"],
            "permanent_bonus": 0.05,
        }


class CrateOpenRequest(BaseModel):
    """Payload para abrir uma crate."""

    model_config = ConfigDict(extra="forbid")

    username: Username
    use_free: bool = False  # True = usar crate grátis, False = comprar


@app.post("/api/v1/networks/{realm_id}/crates/open", tags=["Crates"])
async def open_crate(realm_id: str, data: CrateOpenRequest) -> dict[str, Any]:
    """Abre uma Mempool Crate e retorna o item dropado.

    O jogador pode abrir uma crate grátis (se tiver disponivel) ou comprar
    uma por 5.000 sats.

    Args:
        realm_id: Identificador do realm.
        data: Payload com ``username`` e ``use_free``.

    Returns:
        Dict com ``item`` dropado, ``crates_remaining`` e ``balance``.

    Raises:
        HTTPException: Se o jogador não tiver crates disponíveis ou saldo.
    """
    definition = get_network_definition(realm_id)
    crate_key = crates_key(definition.realm_id, data.username)
    player_key = player_state_key(definition.realm_id, data.username)

    # Lê estado atual das crates
    crate_state = await redis_client.hgetall(crate_key)
    free_crates = int(crate_state.get("free_crates", 0))
    owned_crates = int(crate_state.get("owned_crates", 0))
    legendary_bonus = float(crate_state.get("legendary_bonus", 0))

    # Lê saldo do jogador
    player_state = await redis_client.hgetall(player_key)
    balance = int(player_state.get("balance", 0))

    if data.use_free:
        if free_crates <= 0:
            raise HTTPException(status_code=400, detail="Nenhuma crate grátis disponível")
        await redis_client.hincrby(crate_key, "free_crates", -1)
    else:
        price = CRATE_PRICES["crate"]
        if balance < price:
            raise HTTPException(status_code=400, detail=f"Saldo insuficiente. Precisa de {price:,} sats")
        # Debita saldo
        new_balance = balance - price
        await redis_client.hset(player_key, "balance", str(new_balance))
        await redis_client.expire(player_key, 86400)

    # Rola o item
    item = _roll_crate_item()

    # Se for sats, adiciona ao saldo
    if item["type"] == "sats":
        current_balance = int(await redis_client.hget(player_key, "balance") or 0)
        new_balance = current_balance + item["value"]
        await redis_client.hset(player_key, "balance", str(new_balance))
        await redis_client.expire(player_key, 86400)
        item["balance"] = new_balance

    # Se for legendário, acumula bônus permanente
    if item["type"] == "legendary":
        legendary_bonus += item.get("permanent_bonus", 0)
        await redis_client.hset(crate_key, "legendary_bonus", str(legendary_bonus))

    # Salva item no inventário (histórico)
    inventory_raw = crate_state.get("inventory", "[]")
    try:
        inventory = json.loads(inventory_raw)
    except (json.JSONDecodeError, TypeError):
        inventory = []
    inventory.append({
        "item": item,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    })
    # Mantém apenas os últimos 50 itens
    if len(inventory) > 50:
        inventory = inventory[-50:]
    await redis_client.hset(crate_key, "inventory", json.dumps(inventory))
    await redis_client.expire(crate_key, 86400)

    # Retorna resultado
    return {
        "item": item,
        "crates_remaining": {
            "free": int(await redis_client.hget(crate_key, "free_crates") or 0),
            "owned": int(await redis_client.hget(crate_key, "owned_crates") or 0),
        },
        "legendary_bonus": legendary_bonus,
    }


@app.get("/api/v1/networks/{realm_id}/crates/inventory", tags=["Crates"])
async def get_crate_inventory(realm_id: str, username: str) -> dict[str, Any]:
    """Retorna o inventário de crates e itens do jogador.

    Args:
        realm_id: Identificador do realm.
        username: Nome do minerador.

    Returns:
        Dict com ``free_crates``, ``owned_crates``, ``legendary_bonus``,
        ``inventory`` (histórico de itens) e ``crate_price``.
    """
    definition = get_network_definition(realm_id)
    crate_key = crates_key(definition.realm_id, username)

    crate_state = await redis_client.hgetall(crate_key)
    free_crates = int(crate_state.get("free_crates", 0))
    owned_crates = int(crate_state.get("owned_crates", 0))
    legendary_bonus = float(crate_state.get("legendary_bonus", 0))

    inventory_raw = crate_state.get("inventory", "[]")
    try:
        inventory = json.loads(inventory_raw)
    except (json.JSONDecodeError, TypeError):
        inventory = []

    return {
        "realm_id": definition.realm_id,
        "username": username,
        "free_crates": free_crates,
        "owned_crates": owned_crates,
        "legendary_bonus": legendary_bonus,
        "inventory": inventory,
        "crate_price": CRATE_PRICES["crate"],
    }


class CrateClaimRequest(BaseModel):
    """Payload para reclamar crates grátis baseadas em blocos minerados."""

    model_config = ConfigDict(extra="forbid")

    username: Username
    blocks_mined: int


@app.post("/api/v1/networks/{realm_id}/crates/claim", tags=["Crates"])
async def claim_free_crates(realm_id: str, data: CrateClaimRequest) -> dict[str, Any]:
    """Reclama crates grátis acumuladas a cada 10 blocos minerados.

    O jogador ganha 1 crate grátis a cada 10 blocos completados.
    Este endpoint calcula quantas crates o jogador ganhou desde a última
    reclamação e as adiciona ao saldo de free_crates.

    Args:
        realm_id: Identificador do realm.
        data: Payload com ``username`` e ``blocks_mined`` (total de blocos).

    Returns:
        Dict com ``crates_awarded``, ``free_crates`` e ``last_free_block``.
    """
    definition = get_network_definition(realm_id)
    crate_key = crates_key(definition.realm_id, data.username)

    # Lê último bloco onde recebeu crate grátis
    crate_state = await redis_client.hgetall(crate_key)
    last_free_block = int(crate_state.get("last_free_block", 0))
    free_crates = int(crate_state.get("free_crates", 0))

    # Calcula quantas crates novas o jogador ganhou
    blocks_since = data.blocks_mined - last_free_block
    crates_earned = max(0, blocks_since // CRATE_FREE_INTERVAL)

    if crates_earned > 0:
        # Atualiza contadores
        new_free = free_crates + crates_earned
        await redis_client.hset(crate_key, mapping={
            "free_crates": str(new_free),
            "last_free_block": str(data.blocks_mined),
        })
        await redis_client.expire(crate_key, 86400)
        logger.info(
            "Crate grátis: %s ganhou %d crate(s) (blocos %d -> %d)",
            data.username, crates_earned, last_free_block, data.blocks_mined,
        )

    return {
        "crates_awarded": crates_earned,
        "free_crates": free_crates + crates_earned,
        "last_free_block": data.blocks_mined,
    }


# Fase 10: Staking de Sats — modelos Pydantic
class StakeRequest(BaseModel):
    """Payload para travar sats em stake."""

    model_config = ConfigDict(extra="forbid")

    username: Username
    amount: int = Field(strict=True, ge=1000, le=MAX_SCORE)
    duration_hours: int = Field(strict=True, ge=1, le=24)


class StakeResponse(BaseModel):
    """Resposta de stake realizado."""

    username: str
    amount: int
    duration_hours: int
    bonus_percent: float
    start_time: int
    end_time: int


class StakeStatusResponse(BaseModel):
    """Status do stake atual do jogador."""

    username: str
    active: bool
    amount: int | None = None
    duration_hours: int | None = None
    bonus_percent: float | None = None
    start_time: int | None = None
    end_time: int | None = None
    time_remaining_seconds: int | None = None


# Tabela de bônus por duração do stake
STAKE_BONUS_TABLE = {
    1: 0.05,   # 1h: +5% de recompensa
    6: 0.15,   # 6h: +15% de recompensa
    24: 0.30,  # 24h: +30% de recompensa
}
STAKE_PENALTY_PERCENT = 0.10  # 10% de penalty por cancelar antecipadamente


@app.post("/api/v1/networks/{realm_id}/staking/stake", tags=["Staking"])
async def stake_sats(realm_id: str, data: StakeRequest) -> dict[str, Any]:
    """Trava sats em stake por um período determinado.

    O jogador escolhe uma duração (1h, 6h, ou 24h) e recebe um bônus
    passivo de recompensa durante todo o período. Cancelar antecipadamente
    resulta em perda de 10% dos sats staked.

    Args:
        realm_id: Identificador do realm.
        data: Payload com ``username``, ``amount`` e ``duration_hours``.

    Returns:
        Dict com detalhes do stake realizado.

    Raises:
        HTTPException: Se o jogador já tiver stake ativo (409), saldo
            insuficiente (400), ou duração inválida (400).
    """
    definition = get_network_definition(realm_id)
    stake_key = staking_key(definition.realm_id, data.username)
    player_key = player_state_key(definition.realm_id, data.username)

    # Verifica se já há stake ativo
    existing = await redis_client.hgetall(stake_key)
    if existing:
        end_time = int(existing.get("end_time", 0))
        if end_time > int(datetime.datetime.now(datetime.timezone.utc).timestamp()):
            raise HTTPException(
                status_code=409,
                detail="Já existe um stake ativo. Aguarde a expiração ou cancele.",
            )
        # Stake expirado — limpa
        await redis_client.delete(stake_key)

    # Verifica duração válida
    if data.duration_hours not in STAKE_BONUS_TABLE:
        raise HTTPException(
            status_code=400,
            detail="Duração inválida. Use 1, 6 ou 24 horas.",
        )

    # Verifica saldo suficiente
    player_raw = await redis_client.hgetall(player_key)
    current_balance = int(player_raw.get("balance", 0))
    if current_balance < data.amount:
        raise HTTPException(
            status_code=400,
            detail=f"Saldo insuficiente. Saldo: {current_balance}, Necessário: {data.amount}",
        )

    # Deduz do saldo do jogador
    new_balance = current_balance - data.amount
    await redis_client.hset(player_key, mapping={"balance": str(new_balance)})
    await redis_client.expire(player_key, 86400)

    # Calcula tempos e bônus
    now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    duration_seconds = data.duration_hours * 3600
    end_time = now + duration_seconds
    bonus_percent = STAKE_BONUS_TABLE[data.duration_hours]

    # Grava stake no Redis Hash
    await redis_client.hset(stake_key, mapping={
        "amount": str(data.amount),
        "duration_hours": str(data.duration_hours),
        "start_time": str(now),
        "end_time": str(end_time),
        "bonus_percent": str(bonus_percent),
    })
    await redis_client.expire(stake_key, duration_seconds + 3600)  # TTL = duração + 1h de margem

    logger.info(
        "Stake realizado: %s travou %d sats por %dh (+.1f%% bonus)",
        data.username, data.amount, data.duration_hours, bonus_percent * 100,
    )

    return {
        "username": data.username,
        "amount": data.amount,
        "duration_hours": data.duration_hours,
        "bonus_percent": bonus_percent,
        "start_time": now,
        "end_time": end_time,
    }


@app.post("/api/v1/networks/{realm_id}/staking/unstake", tags=["Staking"])
async def unstake_sats(realm_id: str, data: StakeRequest) -> dict[str, Any]:
    """Libera sats staked antecipadamente, aplicando penalty de 10%.

    O jogador perde 10% dos sats staked como penalty por cancelar antes
    do prazo. Os 90% restantes são devolvidos ao saldo.

    Args:
        realm_id: Identificador do realm.
        data: Payload com ``username``.

    Returns:
        Dict com ``returned``, ``penalty`` e ``new_balance``.

    Raises:
        HTTPException: Se não houver stake ativo (404).
    """
    definition = get_network_definition(realm_id)
    stake_key = staking_key(definition.realm_id, data.username)
    player_key = player_state_key(definition.realm_id, data.username)

    # Lê stake ativo
    stake_data = await redis_client.hgetall(stake_key)
    if not stake_data:
        raise HTTPException(status_code=404, detail="Nenhum stake ativo encontrado")

    amount = int(stake_data.get("amount", 0))
    if amount <= 0:
        await redis_client.delete(stake_key)
        raise HTTPException(status_code=404, detail="Nenhum stake ativo encontrado")

    # Calcula penalty e retorno
    penalty = int(amount * STAKE_PENALTY_PERCENT)
    returned = amount - penalty

    # Devolve ao saldo do jogador
    player_raw = await redis_client.hgetall(player_key)
    current_balance = int(player_raw.get("balance", 0))
    new_balance = current_balance + returned
    await redis_client.hset(player_key, mapping={"balance": str(new_balance)})
    await redis_client.expire(player_key, 86400)

    # Adiciona ao histórico
    history_entry = {
        "type": "unstake",
        "amount": amount,
        "penalty": penalty,
        "returned": returned,
        "timestamp": int(datetime.datetime.now(datetime.timezone.utc).timestamp()),
    }
    history_key = staking_history_key(definition.realm_id, data.username)
    await redis_client.rpush(history_key, json.dumps(history_entry))
    await redis_client.ltrim(history_key, 0, 49)  # Mantém no máximo 50 entradas
    await redis_client.expire(history_key, 86400 * 30)  # 30 dias

    # Remove stake ativo
    await redis_client.delete(stake_key)

    logger.info(
        "Unstake com penalty: %s recebeu %d sats (penalty: %d)",
        data.username, returned, penalty,
    )

    return {
        "username": data.username,
        "amount_staked": amount,
        "penalty": penalty,
        "returned": returned,
        "new_balance": new_balance,
    }


@app.get("/api/v1/networks/{realm_id}/staking/status/{username}", tags=["Staking"])
async def get_staking_status(realm_id: str, username: str) -> dict[str, Any]:
    """Retorna o status atual do stake do jogador.

    Args:
        realm_id: Identificador do realm.
        username: Nome do minerador.

    Returns:
        Dict com ``active``, ``amount``, ``duration_hours``, ``bonus_percent``,
        ``start_time``, ``end_time`` e ``time_remaining_seconds``.
    """
    definition = get_network_definition(realm_id)
    stake_key = staking_key(definition.realm_id, username)

    stake_data = await redis_client.hgetall(stake_key)
    now = int(datetime.datetime.now(datetime.timezone.utc).timestamp())

    if not stake_data:
        return {
            "username": username,
            "active": False,
        }

    amount = int(stake_data.get("amount", 0))
    end_time = int(stake_data.get("end_time", 0))
    start_time = int(stake_data.get("start_time", 0))
    duration_hours = int(stake_data.get("duration_hours", 0))
    bonus_percent = float(stake_data.get("bonus_percent", 0))
    time_remaining = max(0, end_time - now)

    # Se expirou, libera automaticamente
    if time_remaining <= 0:
        await redis_client.delete(stake_key)
        # Devolve ao jogador (sem penalty — expirou naturalmente)
        player_key = player_state_key(definition.realm_id, username)
        player_raw = await redis_client.hgetall(player_key)
        current_balance = int(player_raw.get("balance", 0))
        new_balance = current_balance + amount
        await redis_client.hset(player_key, mapping={"balance": str(new_balance)})
        await redis_client.expire(player_key, 86400)

        # Registra no histórico
        history_entry = {
            "type": "expired",
            "amount": amount,
            "timestamp": now,
        }
        history_key = staking_history_key(definition.realm_id, username)
        await redis_client.rpush(history_key, json.dumps(history_entry))
        await redis_client.ltrim(history_key, 0, 49)
        await redis_client.expire(history_key, 86400 * 30)

        logger.info("Stake expirado: %s recebeu %d sats de volta", username, amount)

        return {
            "username": username,
            "active": False,
        }

    return {
        "username": username,
        "active": True,
        "amount": amount,
        "duration_hours": duration_hours,
        "bonus_percent": bonus_percent,
        "start_time": start_time,
        "end_time": end_time,
        "time_remaining_seconds": time_remaining,
    }


@app.get("/api/v1/networks/{realm_id}/staking/history/{username}", tags=["Staking"])
async def get_staking_history(realm_id: str, username: str) -> dict[str, Any]:
    """Retorna o histórico de stakes do jogador.

    Args:
        realm_id: Identificador do realm.
        username: Nome do minerador.

    Returns:
        Dict com ``username`` e ``history`` (lista de entradas).
    """
    definition = get_network_definition(realm_id)
    history_key = staking_history_key(definition.realm_id, username)

    raw_entries = await redis_client.lrange(history_key, 0, -1)
    history = []
    for entry in raw_entries:
        try:
            history.append(json.loads(entry))
        except (json.JSONDecodeError, TypeError):
            continue

    return {
        "username": username,
        "history": history,
    }


# ==========================================================================
# Fase 11: Sistema de Amigos & Co-op — endpoints REST
# ==========================================================================

class FriendAddRequest(BaseModel):
    """Solicitação para adicionar um amigo."""

    model_config = ConfigDict(extra="forbid")

    username: Username
    friend_username: Username


class FriendRemoveRequest(BaseModel):
    """Solicitação para remover um amigo."""

    model_config = ConfigDict(extra="forbid")

    username: Username
    friend_username: Username


# Limite de tempo para considerar um jogador "online" (segundos)
ONLINE_TIMEOUT_SECONDS = 30


async def _get_online_players(realm_id: str) -> dict[str, float]:
    """Retorna dicionário de jogadores online com timestamps."""
    key = online_key(realm_id)
    raw = await redis_client.hgetall(key)
    now = datetime.datetime.now(datetime.timezone.utc).timestamp()
    online = {}
    for username, ts_str in raw.items():
        try:
            ts = float(ts_str)
            if now - ts < ONLINE_TIMEOUT_SECONDS:
                online[username] = ts
        except (ValueError, TypeError):
            continue
    return online


async def _get_player_level(realm_id: str, username: str) -> int:
    """Retorna o nível do jogador (padrão 1 se não encontrado)."""
    key = level_key(realm_id, username)
    raw = await redis_client.hgetall(key)
    if raw:
        try:
            return int(raw.get("level", 1))
        except (ValueError, TypeError):
            pass
    return 1


@app.post("/api/v1/networks/{realm_id}/friends/add", tags=["Amigos"])
async def add_friend(realm_id: str, data: FriendAddRequest) -> dict[str, Any]:
    """Adiciona um jogador à lista de amigos.

    Args:
        realm_id: Identificador do realm.
        data: Payload com ``username`` e ``friend_username``.

    Returns:
        Dict com status e lista de amigos atualizada.

    Raises:
        HTTPException: Se tentar adicionar a si mesmo ou se o amigo já existe.
    """
    definition = get_network_definition(realm_id)
    username = data.username
    friend_username = data.friend_username

    if username == friend_username:
        raise HTTPException(status_code=400, detail="Não pode adicionar a si mesmo")

    key = friends_key(definition.realm_id, username)
    already_exists = await redis_client.sismember(key, friend_username)
    if already_exists:
        raise HTTPException(status_code=400, detail="Amigo já na lista")

    await redis_client.sadd(key, friend_username)
    await redis_client.expire(key, 86400 * 30)  # 30 dias TTL

    logger.info("Amigo adicionado: %s -> %s em %s", username, friend_username, definition.realm_id)

    # Retorna lista atualizada
    return await _get_friends_list(definition.realm_id, username)


@app.post("/api/v1/networks/{realm_id}/friends/remove", tags=["Amigos"])
async def remove_friend(realm_id: str, data: FriendRemoveRequest) -> dict[str, Any]:
    """Remove um jogador da lista de amigos.

    Args:
        realm_id: Identificador do realm.
        data: Payload com ``username`` e ``friend_username``.

    Returns:
        Dict com status e lista de amigos atualizada.
    """
    definition = get_network_definition(realm_id)
    username = data.username
    friend_username = data.friend_username

    key = friends_key(definition.realm_id, username)
    removed = await redis_client.srem(key, friend_username)

    if not removed:
        raise HTTPException(status_code=404, detail="Amigo não encontrado na lista")

    logger.info("Amigo removido: %s -> %s em %s", username, friend_username, definition.realm_id)

    return await _get_friends_list(definition.realm_id, username)


async def _get_friends_list(realm_id: str, username: str) -> dict[str, Any]:
    """Retorna a lista de amigos com status online, nível e realm."""
    key = friends_key(realm_id, username)
    friend_names = await redis_client.smembers(key)

    online_players = await _get_online_players(realm_id)

    friends = []
    for friend_name in friend_names:
        is_online = friend_name in online_players
        level = await _get_player_level(realm_id, friend_name)
        friends.append({
            "username": friend_name,
            "online": is_online,
            "level": level,
            "realm_id": realm_id,
        })

    # Calcula bônus co-op: +5% por amigo online, máx +20% (4 amigos)
    online_count = sum(1 for f in friends if f["online"])
    co_op_bonus = min(online_count * 0.05, 0.20)

    return {
        "username": username,
        "realm_id": realm_id,
        "friends": friends,
        "online_count": online_count,
        "co_op_bonus": co_op_bonus,
    }


@app.get("/api/v1/networks/{realm_id}/friends/{username}", tags=["Amigos"])
async def get_friends(realm_id: str, username: str) -> dict[str, Any]:
    """Retorna a lista de amigos do jogador com status online e bônus co-op.

    Args:
        realm_id: Identificador do realm.
        username: Nome do minerador.

    Returns:
        Dict com ``username``, ``friends`` (lista com status), ``online_count``,
        e ``co_op_bonus`` (fração, ex: 0.15 = 15%).
    """
    definition = get_network_definition(realm_id)
    return await _get_friends_list(definition.realm_id, username)


# ==========================================================================
# Fase 11: Energy System — endpoints REST
# ==========================================================================

ENERGY_MAX = 10
ENERGY_REFILL_INTERVAL = 1800  # 30 min em segundos
ENERGY_BUY_COST = 2000  # sats por 3 energy
ENERGY_BUY_AMOUNT = 3


@app.get("/api/v1/networks/{realm_id}/energy/status", tags=["Energy"])
async def get_energy_status(realm_id: str, username: str) -> dict[str, Any]:
    """Retorna o estado de energia do jogador com regeneração calculada.

    Args:
        realm_id: Identificador do realm.
        username: Nome do minerador.

    Returns:
        Dict com ``current``, ``max``, ``next_refill_at`` (timestamp UNIX),
        e ``seconds_until_refill`` (segundos até a próxima regeneração).
    """
    definition = get_network_definition(realm_id)
    key = energy_key(definition.realm_id, username)
    raw = await redis_client.hgetall(key)

    now = datetime.datetime.now(datetime.timezone.utc).timestamp()

    if not raw:
        # Primeiro acesso — inicializa com energia máxima
        await redis_client.hset(key, mapping={
            "current": ENERGY_MAX,
            "last_refill": str(now),
            "max": str(ENERGY_MAX),
        })
        await redis_client.expire(key, 86400 * 30)  # 30 dias TTL
        return {
            "username": username,
            "current": ENERGY_MAX,
            "max": ENERGY_MAX,
            "next_refill_at": now + ENERGY_REFILL_INTERVAL,
            "seconds_until_refill": ENERGY_REFILL_INTERVAL,
        }

    current = int(raw.get("current", ENERGY_MAX))
    energy_max = int(raw.get("max", ENERGY_MAX))
    last_refill = float(raw.get("last_refill", now))

    # Calcula regeneração automática
    elapsed = now - last_refill
    refills = int(elapsed // ENERGY_REFILL_INTERVAL)
    if refills > 0:
        current = min(current + refills, energy_max)
        last_refill += refills * ENERGY_REFILL_INTERVAL
        await redis_client.hset(key, mapping={
            "current": str(current),
            "last_refill": str(last_refill),
        })

    next_refill_at = last_refill + ENERGY_REFILL_INTERVAL
    seconds_until_refill = max(0, next_refill_at - now)

    return {
        "username": username,
        "current": current,
        "max": energy_max,
        "next_refill_at": next_refill_at,
        "seconds_until_refill": seconds_until_refill,
    }


@app.post("/api/v1/networks/{realm_id}/energy/spend", tags=["Energy"])
async def spend_energy(realm_id: str, username: str) -> dict[str, Any]:
    """Gasta 1 energy para iniciar uma nova rodada.

    Args:
        realm_id: Identificador do realm.
        username: Nome do minerador.

    Returns:
        Dict com ``current`` após o gasto.

    Raises:
        HTTPException: Se não houver energia suficiente (status 400).
    """
    definition = get_network_definition(realm_id)
    key = energy_key(definition.realm_id, username)
    raw = await redis_client.hgetall(key)

    now = datetime.datetime.now(datetime.timezone.utc).timestamp()

    if not raw:
        await redis_client.hset(key, mapping={
            "current": str(ENERGY_MAX),
            "last_refill": str(now),
            "max": str(ENERGY_MAX),
        })
        await redis_client.expire(key, 86400 * 30)
        return {"username": username, "current": ENERGY_MAX - 1}

    current = int(raw.get("current", ENERGY_MAX))
    energy_max = int(raw.get("max", ENERGY_MAX))
    last_refill = float(raw.get("last_refill", now))

    # Regenera antes de gastar
    elapsed = now - last_refill
    refills = int(elapsed // ENERGY_REFILL_INTERVAL)
    if refills > 0:
        current = min(current + refills, energy_max)
        last_refill += refills * ENERGY_REFILL_INTERVAL

    if current <= 0:
        raise HTTPException(status_code=400, detail="Energia insuficiente")

    current -= 1
    await redis_client.hset(key, mapping={
        "current": str(current),
        "last_refill": str(last_refill),
    })

    return {"username": username, "current": current}


@app.post("/api/v1/networks/{realm_id}/energy/buy", tags=["Energy"])
async def buy_energy(realm_id: str, username: str) -> dict[str, Any]:
    """Compra 3 energy por 2.000 sats.

    Args:
        realm_id: Identificador do realm.
        username: Nome do minerador.

    Returns:
        Dict com ``current`` após a compra.

    Raises:
        HTTPException: Se saldo insuficiente ou já no máximo (status 400).
    """
    definition = get_network_definition(realm_id)

    # Verifica saldo do jogador
    state_key = player_state_key(definition.realm_id, username)
    state_raw = await redis_client.hgetall(state_key)
    balance = int(state_raw.get("balance", 0))

    if balance < ENERGY_BUY_COST:
        raise HTTPException(
            status_code=400,
            detail=f"Saldo insuficiente. Necessario {ENERGY_BUY_COST} sats",
        )

    # Debita saldo
    new_balance = balance - ENERGY_BUY_COST
    await redis_client.hset(state_key, mapping={"balance": str(new_balance)})

    # Adiciona energia
    energy_key_str = energy_key(definition.realm_id, username)
    raw = await redis_client.hgetall(energy_key_str)
    now = datetime.datetime.now(datetime.timezone.utc).timestamp()

    if not raw:
        await redis_client.hset(energy_key_str, mapping={
            "current": str(ENERGY_BUY_AMOUNT),
            "last_refill": str(now),
            "max": str(ENERGY_MAX),
        })
        await redis_client.expire(energy_key_str, 86400 * 30)
        return {"username": username, "current": ENERGY_BUY_AMOUNT, "balance": new_balance}

    current = int(raw.get("current", 0))
    energy_max = int(raw.get("max", ENERGY_MAX))
    last_refill = float(raw.get("last_refill", now))

    # Regenera antes de comprar
    elapsed = now - last_refill
    refills = int(elapsed // ENERGY_REFILL_INTERVAL)
    if refills > 0:
        current = min(current + refills, energy_max)
        last_refill += refills * ENERGY_REFILL_INTERVAL

    if current >= energy_max:
        # Reverte saldo se já está no máximo
        await redis_client.hset(state_key, mapping={"balance": str(balance)})
        raise HTTPException(status_code=400, detail="Energia já no máximo")

    current = min(current + ENERGY_BUY_AMOUNT, energy_max)
    await redis_client.hset(energy_key_str, mapping={
        "current": str(current),
        "last_refill": str(last_refill),
    })

    return {"username": username, "current": current, "balance": new_balance}


# ==========================================================================
# Mini-game Decoder — adivinhar palavra BIP39 a partir do TXID truncado
# ==========================================================================

# Lista de palavras BIP39 em português (subconjunto para o mini-game)
BIP39_WORDLIST = [
    "abismo", "abotoar", "abrir", "absoluto", "abster", "acabado", "acalmar",
    "acampar", "acender", "acervo", "acertar", "acessar", "achar", "acima",
    "acionar", "acordar", "acumular", "adaptar", "adega", "adepto", "adequar",
    "aderir", "adesivo", "adeus", "adiante", "aditivo", "adjetivo", "adjunto",
    "admirar", "admoestar", "adotar", "adquirir", "advogado", "aereo", "afastar",
    "afeicao", "afetivo", "afim", "afinal", "aflito", "afluente", "afogar",
    "afeto", "afoito", "afora", "afresco", "afrontar", "agachar",
    "agarrar", "agasalho", "agente", "agilizar", "agitar", "agora", "agradar",
    "agreste", "agrupar", "agua", "agudo", "agulha", "alavanca", "alarme",
    "albergar", "albino", "album", "alecrim", "alegria",
    "alerta", "alface", "algar", "algum", "alheio", "aliar", "alicate",
    "alimento", "alinhar", "aliviar", "almofada", "aloccar",
    "alpiste", "alterar", "altitude", "alto", "alucinar", "alugar", "aluno",
    "alusivo", "alvo", "amador", "amarelo", "amassar", "amendoim", "amenizar",
    "amigo", "amistoso", "amolar", "amontoar", "amor", "amparar", "ampliar",
    "ampola", "anagrama", "analisar", "anarquia", "anatomia", "andaime",
    "andar", "anel", "anexo", "anjo", "anomalia", "anotacao", "ansioso",
    "anterior", "antigo", "antologia", "antraz", "anual", "anverso",
    "anzol", "apagador", "apalpar", "apanhar", "aparecer", "apaziguar",
    "apego", "apelar", "apelo", "apertar", "apesar", "apetite", "apito",
    "aplauso", "aplicar", "apoderar", "apontar", "apoio", "apoiar", "apolo",
    "aposto", "aprendiz", "aprovar", "aquecer", "aquilo", "arara",
    "arauto", "arbitrio", "ardil", "areia", "arestar", "arguir",
    "arma", "armario", "armazenar", "aroma", "arpendice", "arranhar",
    "arrepender", "arriar", "arroba", "arrumar", "arsenal", "arteria",
    "artigo", "artista", "arvore", "asfaltar", "aspirar", "assador",
    "asilo", "aspirina", "assalto", "assegurar", "assentar", "assinar",
    "assoalho", "assunto", "astral", "astuto", "atalho", "atadura",
    "atarefar", "atear", "atender", "aterro", "ateu", "atestado",
    "aterrar", "atlas", "atmosfera", "atolar", "atordoar", "atracar",
    "atrasar", "atrevido", "atriz", "atual", "atum", "auditor",
    "aumentar", "aura", "aurora", "autismo", "autoria", "autuar",
    "avaliar", "avante", "avaria", "avaro", "ave", "avena",
    "avesso", "avistar", "avivar", "avulso", "axila", "azarar",
    "azedo", "azulejo", "babar", "bacalhau", "bacharel", "bacia",
    "bagagem", "baiano", "bailar", "baioneta", "bairro", "baixar",
    "bajular", "bala", "balada", "balanco", "balao", "balde", "baleia",
    "baliza", "bambolear", "banal", "banca", "banco", "bandagem",
    "bangue", "banir", "banquete", "barato", "barba", "barco",
    "baronesa", "barraca", "barulho", "base", "basico", "bastao",
    "batata", "bate", "batida", "batom", "baunilha", "beber",
    "beijo", "beirada", "beisebol", "beldade", "beleza", "belga",
    "beliscar", "bendito", "bengala", "benzer", "berimbau", "berlinde",
    "berro", "bertalha", "besouro", "besta", "betim", "bexiga",
    "bico", "bicudo", "bienal", "bifoco", "bigorna", "bilhete", "bimestre",
    "bimotor", "bipolar", "biruta", "biscoito", "bisneto", "bispo", "bisturi",
    "bitola", "bizarro", "blazer", "boato", "bobagem", "bocado", "bocejar",
    "boicotar", "boiar", "boina", "bolada", "boletim", "boleto", "bolha",
    "bolo", "bolsa", "bomba", "bonde", "boneco", "bonita", "borbulha",
    "borda", "boreal", "borracha", "bovino", "boxear", "branco", "brasa",
    "braveza", "brecha", "breu", "briga", "brilho", "brincar", "broa",
    "broto", "bruxa", "bucha", "budismo", "bufar", "bule", "buraco",
    "busca", "busto", "buzina", "cabana", "cabelo", "cabide", "cabo",
    "cabrito", "cacau", "cacetada", "cachorro", "cacique", "cadeado",
    "cafe", "cagao", "caiaque", "caipira", "caixas", "cajado", "caju",
    "calafrio", "calamar", "calcinar", "calda", "calibrar", "calma",
    "calota", "calvo", "cama", "cambista", "camisa", "camomila", "campanha",
    "camuflar", "canavial", "cancelar", "caneta", "canguru", "canhoto",
    "canibal", "canoa", "canudo", "capaz", "capela", "capinar", "capotar",
    "capricho", "captar", "capuz", "caracol", "caranguejo", "carinho",
    "carneiro", "carpete", "carreira", "cartaz", "carvalho", "casaco",
    "casca", "casebre", "castelo", "casulo", "catarata", "cativar",
    "caule", "causar", "cautela", "cavalo", "caverna", "cebola", "ceder",
    "cegonha", "celebrar", "celula", "cenoura", "censo", "centeio", "ceramica",
    "cerdeira", "cerrado", "certeiro", "cerveja", "cetim", "cevada", "chacota",
    "chaleira", "chamado", "chapu", "charme", "chatice", "chave", "chefe",
    "cheiro", "chicote", "chifre", "chinelo", "chocalho", "chover", "chumbo",
    "chutar", "cicatriz", "ciclone", "cidade", "cidreira", "ciente", "cigana",
    "cima", "cinco", "cine", "cintila", "cinto", "ciranda", "circuito",
    "cirurgia", "citrico", "civil", "clero", "clicar", "clone", "clube",
    "coberto", "cobrar", "coccinela", "coelho", "coentro", "coeso", "cogumelo",
    "coibir", "coifa", "coiote", "colar", "coleira", "colher", "colina",
    "colmo", "colocar", "coluna", "comando", "combinar", "comentar", "cometa",
    "comodo", "concha", "condor", "conectar", "confuso", "congelar", "conhecer",
    "conjugar", "conluio", "conquista", "conserto", "consumir", "contrato",
    "convite", "cooperar", "copeiro", "copiador", "copo", "coquetel", "coragem",
    "corda", "corja", "corneta", "coronha", "corporal", "correio",
    "corte", "coruja", "corvo", "cosseno", "costela", "cotonete", "couve",
    "covil", "cozinha", "cratera", "cravo", "creche", "crespo",
    "crente", "crepite", "crescer", "criar", "crime", "cristal",
    "crosta", "crucifixo", "cruel", "crua", "cruzeiro", "cubano", "cueca",
    "cuidado", "culatra", "culminar", "culpar", "cultura", "cumprir", "cunhado",
    "cupido", "curativo", "curral", "cursar", "curto", "cuspir",
    "custear", "cutucar", "duelar", "duende", "dublador", "dublar", "ducha",
    "duela", "duende", "dublador", "dublar", "duela", "duende",
    "dublador", "dublar", "duela", "duende", "dublador", "dublar",
]

# Cooldown entre partidas do decoder (segundos)
DECODER_COOLDOWN_SECONDS = 180  # 3 minutos


class DecoderStart(BaseModel):
    """Solicitacao para iniciar uma partida do mini-game Decoder."""
    model_config = ConfigDict(extra="forbid")

    username: Username


class DecoderSubmit(BaseModel):
    """Solicitacao para enviar resposta no mini-game Decoder."""
    model_config = ConfigDict(extra="forbid")

    username: Username
    answer: str = Field(min_length=1, max_length=20)


@app.post("/api/v1/networks/{realm_id}/decoder/start", tags=["Decoder"])
async def decoder_start(realm_id: str, data: DecoderStart) -> dict[str, Any]:
    """Inicia uma partida do mini-game Decoder.

    Gera um TXID truncado a partir de uma palavra BIP39 e retorna a dica
    (primeira letra) para o jogador adivinhar.

    Args:
        realm_id: Identificador do realm.
        data: Payload com ``username``.

    Returns:
        Dict com ``tx_stub``, ``first_letter``, ``streak``, ``wins``.

    Raises:
        HTTPException: Se o jogador estiver no cooldown (status 429).
    """
    import time
    definition = get_network_definition(realm_id)
    key = decoder_key(definition.realm_id, data.username)

    # Verifica cooldown
    last_play = await redis_client.hget(key, "last_play")
    if last_play:
        elapsed = time.time() - int(last_play)
        if elapsed < DECODER_COOLDOWN_SECONDS:
            remaining = int(DECODER_COOLDOWN_SECONDS - elapsed)
            raise HTTPException(
                status_code=429,
                detail=f"Aguarde {remaining}s para jogar novamente",
            )

    # Escolhe palavra aleatoria
    word = random.choice(BIP39_WORDLIST)

    # Gera TXID truncado a partir do hash da palavra
    txid_hash = hashlib.sha256(word.encode()).hexdigest()
    tx_stub = f"0x{txid_hash[:4]}...{txid_hash[-4:]}"

    # Primeira letra como dica
    first_letter = word[0].upper()

    # Le streak e wins atuais
    streak_raw = await redis_client.hget(key, "streak")
    wins_raw = await redis_client.hget(key, "wins")
    streak = int(streak_raw) if streak_raw else 0
    wins = int(wins_raw) if wins_raw else 0

    # Armazena a resposta correta em uma chave temporaria (expira em 60s)
    answer_key = f"{key}:pending"
    await redis_client.set(answer_key, word, ex=60)

    # Atualiza timestamp
    await redis_client.hset(key, "last_play", str(int(time.time())))
    await redis_client.expire(key, 86400)

    return {
        "tx_stub": tx_stub,
        "first_letter": first_letter,
        "streak": streak,
        "wins": wins,
    }


@app.post("/api/v1/networks/{realm_id}/decoder/submit", tags=["Decoder"])
async def decoder_submit(realm_id: str, data: DecoderSubmit) -> dict[str, Any]:
    """Envia resposta no mini-game Decoder.

    Valida a resposta do jogador e atualiza streak/wins. Em caso de acerto,
    credita 5.000 sats e um power-up aleatorio.

    Args:
        realm_id: Identificador do realm.
        data: Payload com ``username`` e ``answer``.

    Returns:
        Dict com ``correct``, ``word``, ``streak``, ``wins``, ``bonus_sats``,
        ``powerup_id`` (se acertou).
    """
    definition = get_network_definition(realm_id)
    key = decoder_key(definition.realm_id, data.username)
    answer_key = f"{key}:pending"

    # Recupera resposta correta
    correct_word = await redis_client.get(answer_key)
    if not correct_word:
        raise HTTPException(status_code=400, detail="Sessao expirada. Inicie uma nova partida.")

    # Apaga resposta pendente
    await redis_client.delete(answer_key)

    answer = data.answer.strip().lower()
    is_correct = answer == correct_word.lower()

    if is_correct:
        # Atualiza streak e wins
        streak_raw = await redis_client.hget(key, "streak")
        wins_raw = await redis_client.hget(key, "wins")
        streak = (int(streak_raw) if streak_raw else 0) + 1
        wins = (int(wins_raw) if wins_raw else 0) + 1

        await redis_client.hset(key, mapping={"streak": str(streak), "wins": str(wins)})
        await redis_client.expire(key, 86400)

        # Credita bonus de 5.000 sats no player state
        player_key = player_state_key(definition.realm_id, data.username)
        await redis_client.hincrby(player_key, "balance", 5000)
        await redis_client.expire(player_key, 86400)

        # Concede power-up aleatorio
        powerup_id = random.choice(list(POWERUP_IDS))
        await redis_client.hincrby(key.replace("decoder", "powerups"), powerup_id, 1)

        logger.info(
            "Decoder acerto: %s adivinhou %s (streak=%d, wins=%d)",
            data.username, correct_word, streak, wins,
        )

        return {
            "correct": True,
            "word": correct_word,
            "streak": streak,
            "wins": wins,
            "bonus_sats": 5000,
            "powerup_id": powerup_id,
        }

    # Erro: reseta streak
    await redis_client.hset(key, "streak", "0")
    await redis_client.expire(key, 86400)

    logger.info(
        "Decoder erro: %s respondeu %s (correta: %s)",
        data.username, answer, correct_word,
    )

    return {
        "correct": False,
        "word": correct_word,
        "streak": 0,
        "wins": int(await redis_client.hget(key, "wins") or 0),
        "bonus_sats": 0,
        "powerup_id": None,
    }


@app.websocket("/ws/v1/game/{realm_id}")
async def websocket_v1(websocket: WebSocket, realm_id: str) -> None:
    """WebSocket canônico multi-rede."""
    await serve_websocket(websocket, realm_id)


@app.websocket("/ws/game")
async def websocket_legacy(websocket: WebSocket) -> None:
    """Alias temporário restrito ao realm padrão."""
    await serve_websocket(websocket, DEFAULT_REALM_ID)


# ==========================================================================
# Fase 10: Season Pass — Passaporte de Temporada
# ==========================================================================

from app.season_pass import (
    SEASON_FREE_LEVELS,
    SEASON_FREE_REWARDS,
    SEASON_PREMIUM_LEVELS,
    SEASON_PREMIUM_REWARDS,
    SEASON_XP_PER_LEVEL,
    add_season_xp,
    buy_season_premium,
    claim_season_reward,
    get_season_data,
)


@app.get("/api/v1/networks/{realm_id}/season/{username}")
async def get_season_endpoint(realm_id: str, username: str) -> dict[str, Any]:
    """Retorna dados da temporada atual do jogador."""
    try:
        data = await get_season_data(
            realm_id, username, season_key, player_state_key,
            powerups_key, redis_client, get_network_definition
        )
        return data
    except Exception as e:
        logger.error("Erro ao obter dados da temporada: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/networks/{realm_id}/season/{username}/add-xp")
async def add_season_xp_endpoint(realm_id: str, username: str, data: dict[str, Any] = Body(default={"xp": 0})) -> dict[str, Any]:
    """Adiciona XP à temporada do jogador."""
    try:
        xp_amount = data.get("xp", 0)
        result = await add_season_xp(
            realm_id, username, xp_amount, season_key, player_state_key,
            powerups_key, redis_client, get_network_definition
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Erro ao adicionar XP: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/networks/{realm_id}/season/{username}/claim/{reward_level}")
async def claim_season_reward_endpoint(realm_id: str, username: str, reward_level: int) -> dict[str, Any]:
    """Reclama recompensa de um nível da temporada."""
    try:
        result = await claim_season_reward(
            realm_id, username, reward_level, season_key, player_state_key,
            powerups_key, redis_client, get_network_definition
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Erro ao reclamar recompensa: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/networks/{realm_id}/season/{username}/buy-premium")
async def buy_season_premium_endpoint(realm_id: str, username: str) -> dict[str, Any]:
    """Compra acesso premium da temporada (50.000 sats)."""
    try:
        result = await buy_season_premium(
            realm_id, username, season_key, player_state_key,
            powerups_key, redis_client, get_network_definition
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Erro ao comprar premium: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================================================
# Fase 5: Modo Sprint — Rodadas rápidas 10×10, 4 palavras, 30s
# ==========================================================================

from app.storage import sprint_leaderboard_key

SPRINT_GRID_SIZE = 10
SPRINT_WORD_COUNT = 4
SPRINT_TIME_LIMIT = 30
SPRINT_REWARD_MULTIPLIER = 0.5


class SprintStartRequest(BaseModel):
    """Payload estrito para iniciar uma rodada Sprint."""

    model_config = ConfigDict(extra="forbid", strict=True)

    username: Username


class SprintSubmitRequest(BaseModel):
    """Resultado validado de uma rodada Sprint."""

    model_config = ConfigDict(extra="forbid", strict=True)

    username: Username
    words_found: int = Field(ge=0, le=SPRINT_WORD_COUNT)
    time_taken: float = Field(gt=0, le=SPRINT_TIME_LIMIT)


@app.post("/api/v1/networks/{realm_id}/sprint/start")
async def sprint_start(realm_id: str, data: SprintStartRequest) -> dict[str, Any]:
    """Inicia uma rodada sprint."""
    get_network_definition(realm_id)

    # Gera palavras sprint (4 palavras aleatórias do wordlist)
    import random
    words = random.sample(BIP39_WORDLIST, SPRINT_WORD_COUNT)

    return {
        "mode": "sprint",
        "grid_size": SPRINT_GRID_SIZE,
        "words": words,
        "time_limit": SPRINT_TIME_LIMIT,
        "reward_multiplier": SPRINT_REWARD_MULTIPLIER,
    }


@app.post("/api/v1/networks/{realm_id}/sprint/submit")
async def sprint_submit(realm_id: str, data: SprintSubmitRequest) -> dict[str, Any]:
    """Envia resultado de uma rodada sprint."""
    definition = get_network_definition(realm_id)
    username = data.username
    words_found = data.words_found
    time_taken = data.time_taken

    # Calcula recompensa (50% do valor normal)
    base_reward = words_found * 1000  # 1000 sats por palavra
    reward = int(base_reward * SPRINT_REWARD_MULTIPLIER)

    # Atualiza saldo
    ps_key = player_state_key(definition.realm_id, username)
    await redis_client.hincrby(ps_key, "balance", reward)

    # Atualiza leaderboard sprint (ordena por tempo menor)
    sl_key = sprint_leaderboard_key(definition.realm_id)
    await redis_client.zadd(sl_key, {f"{username}:{int(time.time())}": time_taken})
    await redis_client.zremrangebyrank(sl_key, 0, -11)  # Mantém top 10

    return {
        "words_found": words_found,
        "time_taken": time_taken,
        "reward": reward,
    }


@app.get("/api/v1/networks/{realm_id}/sprint/leaderboard")
async def sprint_leaderboard(realm_id: str) -> dict[str, Any]:
    """Retorna leaderboard do modo sprint."""
    definition = get_network_definition(realm_id)
    sl_key = sprint_leaderboard_key(definition.realm_id)

    members = await redis_client.zrange(sl_key, 0, 9, withscores=True)
    leaderboard = []
    for entry, score in members:
        parts = entry.decode() if isinstance(entry, bytes) else entry
        name = parts.split(":")[0]
        leaderboard.append({"username": name, "time": float(score)})

    return {"leaderboard": leaderboard}


# ==========================================================================
# Fase 2: Sistema de Níveis & Rank
# ==========================================================================

# Definições de ranks temáticos
RANK_DEFINITIONS = [
    (1, 9, "Script Kiddie", "🟢", "+1s tempo base por rank"),
    (10, 19, "Node Operator", "🔵", "+1s tempo base por rank"),
    (20, 29, "Hash Crafter", "🟣", "+1s tempo base por rank"),
    (30, 39, "Block Miner", "🟡", "+1s tempo base por rank"),
    (40, 49, "Mempool Hunter", "🔴", "+1s tempo base por rank"),
    (50, 59, "Satoshi Disciple", "🟠", "+1s tempo base por rank"),
    (60, 69, "Chain Validator", "⚪", "+1s tempo base por rank"),
    (70, 79, "Hash Rate Lord", "🟤", "+1s tempo base por rank"),
    (80, 89, "Block King", "👑", "+1s tempo base por rank"),
    (90, 99, "Bitcoin Legend", "💎", "+1s tempo base por rank"),
    (100, 100, "Satoshi", "🏆", "Rank máximo"),
]


def get_rank_for_level(level: int) -> dict:
    """Retorna o rank atual baseado no nível."""
    for min_lvl, max_lvl, name, icon, bonus in RANK_DEFINITIONS:
        if min_lvl <= level <= max_lvl:
            return {"name": name, "icon": icon, "bonus": bonus, "min_level": min_lvl, "max_level": max_lvl}
    return {"name": "Script Kiddie", "icon": "🟢", "bonus": "+1s tempo base por rank", "min_level": 1, "max_level": 9}


def xp_to_next_level(level: int) -> int:
    """Calcula XP necessário para o próximo nível."""
    return level * 100


def get_level_bonus(level: int) -> dict:
    """Retorna bônus passivos do nível atual."""
    rank_info = get_rank_for_level(level)
    time_bonus = min(level, 10)  # Máx +10s
    hint_discount = min((level // 3) * 10, 30)  # Máx 30% desconto
    return {
        "time_bonus_seconds": time_bonus,
        "hint_discount_percent": hint_discount,
        "rank": rank_info,
    }


@app.get("/api/v1/networks/{realm_id}/level/{username}", tags=["Level & Rank"])
async def get_player_level(realm_id: str, username: str) -> dict[str, Any]:
    """Retorna nível, XP e rank do jogador.

    Args:
        realm_id: Identificador do realm.
        username: Nome do minerador.

    Returns:
        Dict com level, xp, xp_to_next, rank, e bônus passivos.
    """
    definition = get_network_definition(realm_id)
    level_key_name = level_key(definition.realm_id, username)

    level_data = await redis_client.hgetall(level_key_name)

    if not level_data:
        # Primeiro acesso — inicializa com nível 1, 0 XP
        initial_data = {"level": "1", "xp": "0"}
        await redis_client.hset(level_key_name, mapping=initial_data)
        level = 1
        xp = 0
    else:
        level = int(level_data.get("level", 1))
        xp = int(level_data.get("xp", 0))

    xp_needed = xp_to_next_level(level)
    rank_info = get_rank_for_level(level)
    bonuses = get_level_bonus(level)

    return {
        "username": username,
        "realm_id": realm_id,
        "level": level,
        "xp": xp,
        "xp_to_next": xp_needed,
        "xp_progress": round((xp / xp_needed) * 100, 1) if xp_needed > 0 else 100,
        "rank": rank_info,
        "bonuses": bonuses,
    }


@app.post("/api/v1/networks/{realm_id}/level/{username}/add-xp", tags=["Level & Rank"])
async def add_xp_to_player(realm_id: str, username: str, data: dict[str, Any]) -> dict[str, Any]:
    """Adiciona XP ao jogador e verifica level-up.

    Args:
        realm_id: Identificador do realm.
        username: Nome do minerador.
        data: Dict com 'xp' (quantidade de XP a adicionar).

    Returns:
        Dict com level anterior, novo nível, XP total, e se houve level-up.
    """
    definition = get_network_definition(realm_id)
    level_key_name = level_key(definition.realm_id, username)
    xp_to_add = data.get("xp", 0)

    if xp_to_add <= 0:
        return {"level": 1, "new_level": 1, "xp": 0, "xp_total": 0, "leveled_up": False}

    level_data = await redis_client.hgetall(level_key_name)
    level = int(level_data.get("level", 1))
    xp = int(level_data.get("xp", 0))

    old_level = level
    xp += xp_to_add

    # Verifica level-up
    leveled_up = False
    while xp >= xp_to_next_level(level):
        xp -= xp_to_next_level(level)
        level += 1
        leveled_up = True

    # Atualiza no Redis
    await redis_client.hset(level_key_name, mapping={"level": str(level), "xp": str(xp)})

    rank_info = get_rank_for_level(level)
    bonuses = get_level_bonus(level)

    return {
        "username": username,
        "old_level": old_level,
        "level": level,
        "xp": xp,
        "xp_total": (old_level * (old_level - 1) * 100 // 2) + xp,
        "xp_to_next": xp_to_next_level(level),
        "leveled_up": leveled_up,
        "rank": rank_info,
        "bonuses": bonuses,
    }
