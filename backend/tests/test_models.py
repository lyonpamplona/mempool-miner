"""Testes dos contratos expostos pela API."""

import asyncio
import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import app.main as main_module
import httpx
import pytest
from app.main import MAX_SCORE, ScoreSubmit, app
from fastapi import HTTPException
from pydantic import ValidationError


def test_decoder_wordlist_is_bip39_english() -> None:
    """Fase 4.4: o decoder usa o BIP39 inglês (mesmo wordlist do jogo principal).

    Antes da correção, o decoder sorteava de um subconjunto português
    (BIP39_WORDLIST mal nomeado). Agora usa Mnemonic("english").wordlist,
    consistente com as palavras derivadas das transações reais (engine.py).
    """
    wordlist = main_module.BIP39_WORDLIST
    # BIP39 EN tem exatamente 2048 palavras
    assert len(wordlist) == 2048
    # Palavras BIP39 EN presentes
    assert "abandon" in wordlist
    assert "zoo" in wordlist
    # Palavras do antigo subconjunto PT ausentes
    assert "abrir" not in wordlist
    assert "amigo" not in wordlist
    # Todas as palavras são strings minúsculas (padrão BIP39)
    assert all(isinstance(w, str) and w == w.lower() for w in wordlist)


def test_score_submit_normalizes_username() -> None:
    """Espaços externos são removidos de um nickname válido."""
    payload = ScoreSubmit(username=" abcdefghijkl ", score=42)
    assert payload.username == "abcdefghijkl"


@pytest.mark.asyncio
async def test_send_chat_message_publishes_to_events_channel(monkeypatch) -> None:
    """Fase 3.1: o endpoint publica chat_message no canal de eventos (broadcast WS).

    Antes da correção, a mensagem só ia para o Redis List (histórico) e o
    frontend só via as próprias mensagens. Agora, após armazenar, o endpoint
    publica um envelope ``chat_message`` no ``events_channel(realm_id)``.
    """
    redis_client = AsyncMock()
    # Rate limit: primeira mensagem liberada (chave inexistente).
    redis_client.get.return_value = None
    monkeypatch.setattr(main_module, "redis_client", redis_client)

    result = await main_module.send_chat_message(
        "regtest", main_module.ChatMessage(username="tester", message="olá mundo")
    )

    assert result["status"] == "success"
    assert result["message"]["username"] == "tester"
    assert result["message"]["message"] == "olá mundo"

    # O publish aconteceu no canal de eventos do realm.
    redis_client.publish.assert_awaited_once()
    channel_arg, payload_arg = redis_client.publish.await_args.args
    assert channel_arg == main_module.events_channel("regtest")
    published = json.loads(payload_arg)
    assert published["action"] == "chat_message"
    assert published["realm_id"] == "regtest"
    assert published["username"] == "tester"
    assert published["message"] == "olá mundo"
    assert "timestamp" in published
    # Envelope público: campos comuns presentes.
    assert published["schema_version"] == 2
    assert published["event_id"]


def test_score_submit_keeps_pool_name_separate_from_username() -> None:
    """Guilda é metadado opcional e não contamina a identidade do jogador."""
    payload = ScoreSubmit(username="Miner", pool_name=" F2POOL ", score=42)

    assert payload.username == "Miner"
    assert payload.pool_name == "F2POOL"


def test_xp_add_request_rejects_float() -> None:
    """Fase 2.2: o payload de XP rejeita float (XP é sempre inteiro)."""
    from app.main import XpAddRequest

    with pytest.raises(ValidationError):
        XpAddRequest(xp=1.5)
    with pytest.raises(ValidationError):
        XpAddRequest(xp=0.0)


def test_xp_add_request_rejects_negative_and_overflow() -> None:
    """Fase 2.2: o payload de XP rejeita negativo e valor acima de MAX_SCORE."""
    from app.main import XpAddRequest

    with pytest.raises(ValidationError):
        XpAddRequest(xp=-1)
    with pytest.raises(ValidationError):
        XpAddRequest(xp=MAX_SCORE + 1)


def test_xp_add_request_accepts_valid_int() -> None:
    """Fase 2.2: int válido (incluindo 0) é aceito."""
    from app.main import XpAddRequest

    assert XpAddRequest(xp=0).xp == 0
    assert XpAddRequest(xp=100).xp == 100


@pytest.mark.asyncio
async def test_submit_score_aggregates_explicit_pool_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Leaderboard de pools usa o campo próprio sem decorar username."""
    redis_client = AsyncMock()
    redis_client.zadd.side_effect = [1, 1]
    monkeypatch.setattr(main_module, "redis_client", redis_client)
    monkeypatch.setattr(
        main_module,
        "network_snapshot",
        AsyncMock(return_value={"playable": True}),
    )
    # Isola a lógica co-op (Fase 2.3): sem amigos online, bônus = 0.
    monkeypatch.setattr(
        main_module, "_calculate_co_op_bonus", AsyncMock(return_value=0.0)
    )

    result = await main_module.submit_score_for_realm(
        "regtest",
        ScoreSubmit(username="Miner", pool_name="F2POOL", score=42),
    )

    assert result["updated"] is True
    assert redis_client.zadd.await_count == 2
    redis_client.zadd.assert_any_await(
        main_module.leaderboard_key("regtest"),
        {"Miner": 42},
        gt=True,
        ch=True,
    )


@pytest.mark.asyncio
async def test_submit_score_applies_co_op_bonus_to_leaderboard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fase 2.3: o bônus co-op (+5% por amigo online) é aplicado ao score.

    Antes da correção, o bônus era calculado/exibido em /friends mas nunca
    aplicado a nenhuma recompensa (cosmético). Agora o score no leaderboard
    recebe o multiplicador (decisão Opção A).
    """
    redis_client = AsyncMock()
    redis_client.zadd.return_value = 1
    monkeypatch.setattr(main_module, "redis_client", redis_client)
    monkeypatch.setattr(
        main_module,
        "network_snapshot",
        AsyncMock(return_value={"playable": True}),
    )
    # 3 amigos online → bônus 15% (3 × 0.05).
    monkeypatch.setattr(
        main_module, "_calculate_co_op_bonus", AsyncMock(return_value=0.15)
    )

    result = await main_module.submit_score_for_realm(
        "regtest",
        ScoreSubmit(username="Miner", score=1000),
    )

    # 1000 × 1.15 = 1150
    assert result["co_op_bonus"] == 0.15
    assert result["effective_score"] == 1150
    redis_client.zadd.assert_awaited_once_with(
        main_module.leaderboard_key("regtest"),
        {"Miner": 1150},
        gt=True,
        ch=True,
    )


@pytest.mark.parametrize("username", ["", "nome<script>", "nome com espaço"])
def test_score_submit_rejects_unsafe_username(username: str) -> None:
    """Nicknames vazios ou com separadores inseguros são recusados."""
    with pytest.raises(ValidationError):
        ScoreSubmit(username=username, score=42)


@pytest.mark.parametrize("score", [-1, MAX_SCORE + 1])
def test_score_submit_rejects_out_of_range_score(score: int) -> None:
    """A API limita a pontuação ao intervalo documentado."""
    with pytest.raises(ValidationError):
        ScoreSubmit(username="Miner", score=score)


@pytest.mark.parametrize(
    "payload",
    [
        {"username": "Miner", "score": "42"},
        {"username": "Miner", "score": True},
        {"username": "Miner", "score": 42, "admin": True},
    ],
)
def test_score_submit_rejects_coercion_and_extra_fields(payload: dict[str, object]) -> None:
    """Tipos ambíguos e campos fora do contrato não são ignorados silenciosamente."""
    with pytest.raises(ValidationError):
        ScoreSubmit.model_validate(payload)


def test_sprint_submit_rejects_impossible_result() -> None:
    """Uma rodada de quatro palavras não pode aceitar pontuação acima de quatro."""
    with pytest.raises(ValidationError):
        main_module.SprintSubmitRequest(
            username="Miner",
            words_found=5,
            time_taken=10,
        )


def test_sprint_submit_accepts_only_base_time_plus_max_skill_bonus() -> None:
    """Mining pode ampliar o Sprint em no máximo cinco segundos."""
    accepted = main_module.SprintSubmitRequest(
        username="Miner",
        words_found=4,
        time_taken=35.0,
    )
    assert accepted.time_taken == 35.0

    with pytest.raises(ValidationError):
        main_module.SprintSubmitRequest(
            username="Miner",
            words_found=4,
            time_taken=35.001,
        )


@pytest.mark.asyncio
async def test_player_update_rejects_username_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """O body não pode atualizar silenciosamente o jogador indicado por outro path."""
    redis_client = AsyncMock()
    redis_client.hgetall.return_value = {}
    monkeypatch.setattr(main_module, "redis_client", redis_client)

    with pytest.raises(HTTPException) as exc_info:
        await main_module.update_player_state(
            "regtest",
            "PathMiner",
            main_module.PlayerStateUpdate(
                username="BodyMiner",
                balance=100,
            ),
        )

    assert exc_info.value.status_code == 409
    redis_client.hset.assert_not_awaited()


@pytest.mark.asyncio
async def test_lifespan_cleans_started_workers_after_partial_startup_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Falha em um scheduler deve encerrar todos os workers já iniciados."""

    class FakeRelay:
        instances: list["FakeRelay"] = []

        def __init__(self, realm_id: str) -> None:
            self.realm_id = realm_id
            self.stopped = False
            self.instances.append(self)

        async def start(self) -> None:
            return None

        async def stop(self) -> None:
            self.stopped = True

    class FakeScheduler:
        instances: list["FakeScheduler"] = []

        def __init__(self, _redis_client, realm_id: str, **_kwargs) -> None:
            self.realm_id = realm_id
            self.stopped = False
            self.instances.append(self)

        async def start(self) -> None:
            if self.realm_id == "second":
                raise RuntimeError("startup failure")

        async def stop(self) -> None:
            self.stopped = True

    redis_client = AsyncMock()
    monkeypatch.setattr(main_module, "redis_client", redis_client)
    monkeypatch.setattr(main_module, "migrate_legacy_default", AsyncMock())
    monkeypatch.setattr(main_module, "EventRelay", FakeRelay)
    monkeypatch.setattr(main_module, "GlobalEventScheduler", FakeScheduler)
    monkeypatch.setattr(
        main_module,
        "NETWORK_CATALOG",
        (SimpleNamespace(realm_id="first"), SimpleNamespace(realm_id="second")),
    )
    main_module._event_relays.clear()

    with pytest.raises(RuntimeError, match="startup failure"):
        async with main_module.lifespan(main_module.app):
            pass

    assert all(relay.stopped for relay in FakeRelay.instances)
    started_scheduler = next(
        scheduler for scheduler in FakeScheduler.instances if scheduler.realm_id == "first"
    )
    assert started_scheduler.stopped is True
    redis_client.aclose.assert_awaited_once()


def test_expected_routes_are_registered() -> None:
    """Healthcheck, leaderboard e WebSocket devem permanecer publicados."""
    paths = {route.path for route in app.routes}
    assert {"/api/health", "/api/leaderboard", "/ws/game"} <= paths
    assert {
        "/api/v1/networks",
        "/api/v1/networks/{realm_id}/leaderboard",
        "/ws/v1/game/{realm_id}",
    } <= paths


def test_automatic_api_docs_are_closed_by_default() -> None:
    """OpenAPI, Swagger e ReDoc exigem habilitação operacional explícita."""
    paths = {route.path for route in app.routes}
    assert app.debug is False
    assert main_module.app.openapi_url is None
    assert {"/openapi.json", "/docs", "/redoc"}.isdisjoint(paths)


@pytest.mark.parametrize(
    "origin",
    [
        "*",
        "null",
        "https://*.example.com",
        "file:///tmp/game.html",
        "https://user:secret@example.com",
        "https://x/a",
    ],
)
def test_origin_normalization_rejects_unsafe_values(origin: str) -> None:
    """Curingas, credenciais e valores que não são uma origem web falham fechado."""
    with pytest.raises(RuntimeError, match="Origem CORS inválida"):
        main_module.normalize_http_origin(origin)


def test_origin_normalization_removes_default_port_and_trailing_slash() -> None:
    """A comparação de Origin usa a serialização canônica do navegador."""
    assert main_module.normalize_http_origin("HTTPS://Example.COM:443/") == "https://example.com"


@pytest.mark.asyncio
async def test_security_headers_cors_and_host_validation() -> None:
    """A borda recusa Host arbitrário e só autoriza a origem configurada."""
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://localhost") as client:
        rejected_host = await client.get(
            "/api/inexistente",
            headers={"Host": "evil.example"},
        )
        assert rejected_host.status_code == 400

        allowed = await client.get(
            "/api/inexistente",
            headers={"Origin": "http://localhost:8010"},
        )
        assert allowed.headers["access-control-allow-origin"] == "http://localhost:8010"
        assert allowed.headers["cache-control"] == "no-store"
        assert allowed.headers["x-content-type-options"] == "nosniff"
        assert allowed.headers["x-frame-options"] == "DENY"
        assert allowed.headers["x-robots-tag"] == "noindex, nofollow"

        denied = await client.get(
            "/api/inexistente",
            headers={"Origin": "https://evil.example"},
        )
        assert "access-control-allow-origin" not in denied.headers


@pytest.mark.asyncio
async def test_legacy_alias_announces_successor(monkeypatch: pytest.MonkeyPatch) -> None:
    """O alias continua funcional sem ficar invisível para clientes em migração."""
    monkeypatch.setattr(main_module.redis_client, "ping", AsyncMock(return_value=True))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://localhost") as client:
        response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.headers["deprecation"] == "true"
    assert "/api/v1/health/live" in response.headers["link"]


@pytest.mark.asyncio
async def test_redis_error_response_does_not_expose_connection_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Falhas da dependência retornam 503 genérico, sem host ou credenciais."""
    failure = main_module.redis.ConnectionError("redis://user:secret@redis-internal:6379")
    monkeypatch.setattr(main_module.redis_client, "ping", AsyncMock(side_effect=failure))

    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://localhost") as client:
        response = await client.get("/api/v1/health/live")

    assert response.status_code == 503
    assert response.json() == {"detail": "Serviço temporariamente indisponível"}
    assert response.headers["retry-after"] == "5"
    assert "secret" not in response.text
    assert "redis-internal" not in response.text


def test_realm_path_must_be_canonical() -> None:
    """Variações de caixa ou espaços não criam aliases implícitos de rota."""
    for realm_id in ("Regtest", " regtest", "regtest ", "../../regtest"):
        with pytest.raises(HTTPException) as error:
            main_module.get_network_definition(realm_id)
        assert error.value.status_code == 404


def test_websocket_origin_uses_the_same_allowlist() -> None:
    """CORS e WebSocket compartilham a política explícita de origens."""
    websocket = MagicMock()
    websocket.headers = {"origin": "http://localhost:8010"}
    assert main_module.websocket_origin_allowed(websocket) is True

    websocket.headers = {"origin": "https://evil.example"}
    assert main_module.websocket_origin_allowed(websocket) is False

    websocket.headers = {}
    assert main_module.websocket_origin_allowed(websocket) is False


def test_public_event_removes_runtime_and_source_identity() -> None:
    """A borda WebSocket não encaminha topologia, token ou métricas da fila."""
    raw_event_id = "regtest-local:private-session:transaction_received:42"
    event = {
        "schema_version": 2,
        "event_id": raw_event_id,
        "action": "transaction_received",
        "node_id": "regtest-local",
        "network": "regtest",
        "chain": "regtest",
        "realm_id": "regtest",
        "source_session": "private-session",
        "source_sequence": 42,
        "observed_at": "2026-08-14T00:00:00+00:00",
        "epoch": "epoch-a",
        "word": "BITCOIN",
        "txid": "ab" * 32,
        "tx_stub": "abababab",
        "is_golden": False,
        "is_high_fee": True,
        "vsize": 100,
        "fee_rate_sat_vb": 25.0,
        "mempool_count": 7,
        "game_mode": "mempool",
        "_runtime_token": "secret-token",
        "queue_depth": 99,
        "rpc_url": "http://private-node:18443",
    }

    public_event = main_module.sanitize_public_event(event, "regtest")

    assert public_event is not None
    assert public_event["word"] == "BITCOIN"
    assert public_event["tx_stub"] == "abababab"
    assert public_event["event_id"] != raw_event_id
    assert len(public_event["event_id"]) == 64
    assert set(public_event) == {
        "schema_version",
        "event_id",
        "action",
        "network",
        "realm_id",
        "epoch",
        "word",
        "txid",
        "tx_stub",
        "is_golden",
        "is_high_fee",
        "vsize",
        "fee_rate_sat_vb",
    }
    assert {
        "chain",
        "observed_at",
        "node_id",
        "source_session",
        "source_sequence",
        "_runtime_token",
        "queue_depth",
        "rpc_url",
        "mempool_count",
        "game_mode",
    }.isdisjoint(public_event)
    assert main_module.sanitize_public_event(event, "signet") is None


def test_serialized_event_rejects_unknown_action() -> None:
    """Mensagens Redis fora do protocolo não atravessam o WebSocket."""
    raw_event = json.dumps({"action": "internal_debug", "realm_id": "regtest", "secret": "value"})
    assert main_module.serialize_public_event(raw_event, "regtest") is None


def test_network_status_event_exposes_only_game_status() -> None:
    """Heartbeat público não carrega contadores, modo ou topologia interna."""
    event = {
        "schema_version": 2,
        "event_id": "regtest-local:status-session",
        "action": "network_status",
        "network": "regtest",
        "chain": "regtest",
        "realm_id": "regtest",
        "observed_at": "2026-08-14T00:00:00+00:00",
        "epoch": "epoch-a",
        "status": "ready",
        "playable": True,
        "initial_block_download": False,
        "verification_progress": 1.0,
        "pruned": False,
        "mempool_count": 7,
        "game_mode": "mempool",
        "node_id": "regtest-local",
    }

    public_event = main_module.sanitize_public_event(event, "regtest")

    assert public_event is not None
    assert set(public_event) == {
        "schema_version",
        "event_id",
        "action",
        "network",
        "realm_id",
        "epoch",
        "status",
        "playable",
        "initial_block_download",
        "verification_progress",
        "pruned",
    }


@pytest.mark.asyncio
async def test_public_network_snapshot_hides_runtime_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Catálogo preserva seleção do jogo sem revelar identidade e estado interno."""
    heartbeat = {
        "node_id": "regtest-local",
        "_runtime_token": "secret-token",
        "status": "ready",
        "playable": True,
        "initial_block_download": False,
        "verification_progress": 1.0,
        "blocks": 999,
        "headers": 1000,
        "prune_height": 50,
        "epoch": "private-best-block",
        "updated_at": "2026-08-14T00:00:00+00:00",
        "game_mode": "mempool",
        "mempool_count": 7,
    }
    monkeypatch.setattr(main_module, "load_json", AsyncMock(return_value=heartbeat))

    snapshot = await main_module.network_snapshot("regtest")

    assert snapshot == {
        "realm_id": "regtest",
        "network": "regtest",
        "display_name": "Regtest local",
        "status": "ready",
        "playable": True,
        "initial_block_download": False,
        "verification_progress": 1.0,
        "pruned": False,
    }

    runtime_snapshot = await main_module.network_snapshot(
        "regtest",
        include_runtime_epoch=True,
    )
    assert runtime_snapshot["epoch"] == "private-best-block"
    assert set(runtime_snapshot) == {*snapshot, "epoch"}


@pytest.mark.asyncio
async def test_readiness_response_is_minimal(monkeypatch: pytest.MonkeyPatch) -> None:
    """Readiness não divulga realm padrão nem saúde detalhada dos nós."""
    monkeypatch.setattr(main_module.redis_client, "ping", AsyncMock(return_value=True))
    assert await main_module.readiness() == {"status": "ready"}


@pytest.mark.asyncio
async def test_unknown_runtime_status_cannot_enable_scoring(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Status interno inesperado não é refletido nem tratado como jogável."""
    heartbeat = {
        "status": "redis://secret@internal",
        "playable": True,
        "initial_block_download": False,
    }
    monkeypatch.setattr(main_module, "load_json", AsyncMock(return_value=heartbeat))

    snapshot = await main_module.network_snapshot("regtest")

    assert snapshot["status"] == "unavailable"
    assert snapshot["playable"] is False
    assert "secret" not in json.dumps(snapshot)


@pytest.mark.asyncio
async def test_ws_sender_filters_each_redis_message() -> None:
    """O fan-out nunca repassa o documento Redis bruto ao navegador."""

    class FakeRelay:
        """Fornece um evento pela fila usada pelo relay persistente."""

        def __init__(self) -> None:
            self._queue = asyncio.Queue()
            self._queue.put_nowait(
                json.dumps(
                    {
                        "schema_version": 2,
                        "event_id": "regtest-local:session:block_mined:7",
                        "action": "block_mined",
                        "node_id": "regtest-local",
                        "network": "regtest",
                        "chain": "regtest",
                        "realm_id": "regtest",
                        "observed_at": "2026-08-14T00:00:00+00:00",
                        "epoch": "block-a",
                        "block_hash": "ab" * 32,
                        "mempool_count": 0,
                        "discarded_backlog": 500,
                        "_runtime_token": "secret",
                    }
                )
            )

        def add_queue(self) -> asyncio.Queue:
            """Retorna a fila única do relay fake (contrato do EventRelay)."""
            return self._queue

        def remove_queue(self, queue: asyncio.Queue) -> None:
            """No-op — o relay fake não gerencia múltiplas filas."""

    websocket = MagicMock()
    websocket.send_text = AsyncMock(side_effect=[None, RuntimeError("closed")])

    await main_module.ws_sender(
        websocket,
        "regtest",
        FakeRelay(),
        heartbeat_interval=0.001,
    )

    sent = json.loads(websocket.send_text.await_args_list[0].args[0])
    assert set(sent) == {
        "schema_version",
        "event_id",
        "action",
        "network",
        "realm_id",
        "epoch",
        "block_hash",
        "mempool_count",
        "discarded_backlog",
    }
    assert sent["action"] == "block_mined"
    assert {
        "chain",
        "observed_at",
        "node_id",
        "_runtime_token",
    }.isdisjoint(sent)


@pytest.mark.asyncio
async def test_public_websocket_handshake_remains_compatible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A origem permitida recebe game_start com epoch, sem identidade do nó."""

    class WaitingPubSub:
        """Mantém o sender vivo até o cliente encerrar o WebSocket."""

        async def subscribe(self, _channel: str) -> None:
            """Simula a assinatura Redis sem I/O externo."""

        async def unsubscribe(self, *_args: Any, **_kwargs: Any) -> None:
            """Simula a remoção da assinatura (compatível com EventRelay.stop)."""

        async def aclose(self) -> None:
            """Simula o fechamento do Pub/Sub."""

        async def get_message(self, **_kwargs: Any) -> None:
            """Sem mensagens — o listener fica ocioso até ser cancelado."""
            await asyncio.sleep(1)

        async def listen(self):
            """Espera indefinidamente até o cancelamento pelo servidor."""
            if False:  # pragma: no cover - transforma a função em gerador assíncrono
                yield None
            await asyncio.Event().wait()

    snapshot = {
        "realm_id": "regtest",
        "network": "regtest",
        "display_name": "Regtest local",
        "status": "ready",
        "playable": True,
        "initial_block_download": False,
        "verification_progress": 1.0,
        "pruned": False,
        "epoch": "block-a",
    }
    monkeypatch.setattr(main_module, "network_snapshot", AsyncMock(return_value=snapshot))
    monkeypatch.setattr(
        main_module.redis_client,
        "pubsub",
        MagicMock(return_value=WaitingPubSub()),
    )
    # Fase A2: mocka a leitura de transações pendentes (replay em game_start)
    monkeypatch.setattr(
        main_module.redis_client,
        "lrange",
        AsyncMock(return_value=[]),
    )

    websocket = MagicMock()
    websocket.headers = {"origin": "http://localhost:8010"}
    websocket.accept = AsyncMock()
    websocket.close = AsyncMock()
    websocket.send_text = AsyncMock()
    websocket.receive = AsyncMock(return_value={"type": "websocket.disconnect"})

    await main_module.serve_websocket(websocket, "regtest")

    event = json.loads(websocket.send_text.await_args.args[0])

    assert event["action"] == "game_start"
    assert event["realm_id"] == "regtest"
    assert event["epoch"] == "block-a"
    assert event["playable"] is True
    assert set(event) == {
        "schema_version",
        "event_id",
        "action",
        "network",
        "realm_id",
        "epoch",
        "status",
        "playable",
        "initial_block_download",
        "verification_progress",
        "pruned",
        "pending_transactions",  # Fase A2: replay de transações pendentes
    }
    assert {
        "node_id",
        "source_session",
        "chain",
        "observed_at",
        "game_mode",
        "mempool_count",
    }.isdisjoint(event)
    websocket.accept.assert_awaited_once()
    websocket.close.assert_not_awaited()


@pytest.mark.asyncio
async def test_public_websocket_disconnect_during_initial_send_is_clean(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cliente que cai após o accept não deve gerar exceção ASGI."""
    snapshot = {
        "realm_id": "regtest",
        "network": "regtest",
        "display_name": "Regtest local",
        "status": "ready",
        "playable": True,
        "initial_block_download": False,
        "verification_progress": 1.0,
        "pruned": False,
        "epoch": "block-a",
    }
    monkeypatch.setattr(main_module, "network_snapshot", AsyncMock(return_value=snapshot))
    monkeypatch.setattr(main_module, "get_relay", AsyncMock(return_value=MagicMock()))
    # Fase A2: mocka a leitura de transações pendentes (replay em game_start)
    monkeypatch.setattr(
        main_module.redis_client,
        "lrange",
        AsyncMock(return_value=[]),
    )

    websocket = MagicMock()
    websocket.headers = {"origin": "http://localhost:8010"}
    websocket.accept = AsyncMock()
    websocket.close = AsyncMock()
    websocket.send_text = AsyncMock(side_effect=RuntimeError("connection closed"))

    await main_module.serve_websocket(websocket, "regtest")

    websocket.accept.assert_awaited_once()
    websocket.send_text.assert_awaited_once()


@pytest.mark.asyncio
async def test_submit_score_reports_an_existing_record_update(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A resposta usa CH para reconhecer a alteração de um membro existente."""
    zadd = AsyncMock(return_value=1)
    monkeypatch.setattr(main_module.redis_client, "zadd", zadd)
    monkeypatch.setattr(
        main_module,
        "network_snapshot",
        AsyncMock(return_value={"playable": True}),
    )
    # Isola a lógica co-op (Fase 2.3): sem amigos online, bônus = 0.
    monkeypatch.setattr(
        main_module, "_calculate_co_op_bonus", AsyncMock(return_value=0.0)
    )

    response = await main_module.submit_score(ScoreSubmit(username="Miner", score=43))

    assert json.loads(response.body) == {"status": "success", "updated": True}
    assert response.headers["sunset"] == '"2027-01-01"'
    zadd.assert_awaited_once_with(
        main_module.leaderboard_key(main_module.DEFAULT_REALM_ID),
        {"Miner": 43},
        gt=True,
        ch=True,
    )
