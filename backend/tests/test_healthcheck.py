"""Testes do healthcheck do ingestor."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ingestor_healthcheck import (
    HEALTHY_STATUSES,
    MAX_HEARTBEAT_AGE_SECONDS,
    check,
)


@pytest.fixture
def _health_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Variáveis de ambiente para o healthcheck."""
    monkeypatch.setenv("NODE_ID", "regtest-test")
    monkeypatch.setenv("REALM_ID", "regtest")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")


@pytest.fixture
def _token_file(tmp_path: Path) -> Path:
    """Token file temporário."""
    token_file = tmp_path / "token"
    token_file.write_text("test-token-123", encoding="utf-8")
    return token_file


@pytest.fixture
def _monkeypatch_token(monkeypatch: pytest.MonkeyPatch, _token_file: Path) -> None:
    """Aponta INGESTOR_TOKEN_FILE para o token temporário."""
    monkeypatch.setenv("INGESTOR_TOKEN_FILE", str(_token_file))


def test_healthy_statuses_contains_ready() -> None:
    """HEALTHY_STATUSES inclui 'ready'."""
    assert "ready" in HEALTHY_STATUSES


def test_healthy_statuses_contains_syncing() -> None:
    """HEALTHY_STATUSES inclui 'syncing'."""
    assert "syncing" in HEALTHY_STATUSES


def test_healthy_statuses_excludes_unavailable() -> None:
    """HEALTHY_STATUSES não inclui 'unavailable'."""
    assert "unavailable" not in HEALTHY_STATUSES


def test_max_heartbeat_age_is_reasonable() -> None:
    """MAX_HEARTBEAT_AGE_SECONDS é maior que o intervalo de heartbeat (10s)."""
    assert MAX_HEARTBEAT_AGE_SECONDS > 10


@pytest.mark.asyncio
async def test_check_raises_when_token_file_missing(_health_env: None) -> None:
    """check() levanta RuntimeError quando token file não existe."""
    monkeypatch_token = patch.dict(
        "os.environ", {"INGESTOR_TOKEN_FILE": "/tmp/nonexistent-token-file"}
    )
    monkeypatch_token.start()
    try:
        with pytest.raises(RuntimeError, match="token local ausente"):
            await check()
    finally:
        monkeypatch_token.stop()


@pytest.mark.asyncio
async def test_check_raises_when_token_file_empty(
    _health_env: None, _token_file: Path, _monkeypatch_token: None
) -> None:
    """check() levanta RuntimeError quando token file está vazio."""
    _token_file.write_text("", encoding="utf-8")

    with pytest.raises(RuntimeError, match="token local vazio"):
        await check()


@pytest.mark.asyncio
async def test_check_raises_when_heartbeat_absent(
    _health_env: None, _monkeypatch_token: None
) -> None:
    """check() levanta RuntimeError quando heartbeat está ausente no Redis."""
    client = AsyncMock()
    client.mget = AsyncMock(return_value=[None, "test-token-123"])
    client.aclose = AsyncMock()

    with patch("app.ingestor_healthcheck.redis.from_url", return_value=client):
        with pytest.raises(RuntimeError, match="heartbeat ausente"):
            await check()


@pytest.mark.asyncio
async def test_check_raises_when_heartbeat_expired(
    _health_env: None, _monkeypatch_token: None
) -> None:
    """check() levanta RuntimeError quando heartbeat está expirado."""
    expired_time = (datetime.now(UTC) - timedelta(seconds=60)).isoformat()
    snapshot = json.dumps({
        "node_id": "regtest-test",
        "realm_id": "regtest",
        "status": "ready",
        "updated_at": expired_time,
        "_runtime_token": "test-token-123",
    })

    client = AsyncMock()
    client.mget = AsyncMock(return_value=[snapshot, "test-token-123"])
    client.aclose = AsyncMock()

    with patch("app.ingestor_healthcheck.redis.from_url", return_value=client):
        with pytest.raises(RuntimeError, match="heartbeat expirado"):
            await check()


@pytest.mark.asyncio
async def test_check_raises_when_status_not_healthy(
    _health_env: None, _monkeypatch_token: None
) -> None:
    """check() levanta RuntimeError quando status não é saudável."""
    now = datetime.now(UTC).isoformat()
    snapshot = json.dumps({
        "node_id": "regtest-test",
        "realm_id": "regtest",
        "status": "unavailable",
        "updated_at": now,
        "_runtime_token": "test-token-123",
    })

    client = AsyncMock()
    client.mget = AsyncMock(return_value=[snapshot, "test-token-123"])
    client.aclose = AsyncMock()

    with patch("app.ingestor_healthcheck.redis.from_url", return_value=client):
        with pytest.raises(RuntimeError, match="não está pronto"):
            await check()


@pytest.mark.asyncio
async def test_check_raises_when_lease_belongs_to_another_instance(
    _health_env: None, _monkeypatch_token: None
) -> None:
    """check() levanta RuntimeError quando lease pertence a outra instância."""
    now = datetime.now(UTC).isoformat()
    snapshot = json.dumps({
        "node_id": "regtest-test",
        "realm_id": "regtest",
        "status": "ready",
        "updated_at": now,
        "_runtime_token": "other-token",
    })

    client = AsyncMock()
    client.mget = AsyncMock(return_value=[snapshot, "other-token"])
    client.aclose = AsyncMock()

    with patch("app.ingestor_healthcheck.redis.from_url", return_value=client):
        with pytest.raises(RuntimeError, match="outra instância"):
            await check()


@pytest.mark.asyncio
async def test_check_passes_when_everything_is_healthy(
    _health_env: None, _monkeypatch_token: None
) -> None:
    """check() passa quando heartbeat, lease e status estão saudáveis."""
    now = datetime.now(UTC).isoformat()
    snapshot = json.dumps({
        "node_id": "regtest-test",
        "realm_id": "regtest",
        "status": "ready",
        "updated_at": now,
        "_runtime_token": "test-token-123",
    })

    client = AsyncMock()
    client.mget = AsyncMock(return_value=[snapshot, "test-token-123"])
    client.aclose = AsyncMock()

    with patch("app.ingestor_healthcheck.redis.from_url", return_value=client):
        # Não deve levantar exceção.
        await check()

    client.aclose.assert_awaited_once()
