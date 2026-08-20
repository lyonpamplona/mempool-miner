"""Fixtures compartilhadas para testes do backend."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from app.config import BitcoinNetwork, NodeConfig


@pytest.fixture(autouse=True)
def _test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isola variáveis de ambiente para todos os testes do módulo.

    Previne vazamento de credenciais do ambiente CI/host e garante
    que testes não dependam de estado global.
    """
    monkeypatch.setenv("RPC_USER", "test_user")
    monkeypatch.setenv("RPC_PASSWORD", "test_password")
    monkeypatch.setenv("REALM_ID", "regtest")
    monkeypatch.setenv("BITCOIN_NETWORK", "regtest")
    monkeypatch.setenv("NODE_ID", "regtest-local")
    monkeypatch.setenv("RPC_HOST", "localhost")
    monkeypatch.setenv("RPC_PORT", "18443")
    monkeypatch.setenv("ZMQ_HOST", "localhost")
    monkeypatch.setenv("ZMQ_PORT", "28332")


@pytest.fixture
def node_config() -> NodeConfig:
    """Cria uma configuracao isolada sem depender do ambiente do host."""
    return NodeConfig(
        node_id="regtest-local",
        realm_id="regtest",
        network=BitcoinNetwork.REGTEST,
        rpc_host="localhost",
        rpc_port=18443,
        zmq_host="localhost",
        zmq_port=28332,
        rpc_user="test_user",
        rpc_password="test_pass",
    )


@pytest.fixture
def mock_redis_client() -> AsyncMock:
    """Cliente Redis mockado com métodos async padrão."""
    client = AsyncMock()
    client.eval = AsyncMock(return_value=1)
    client.mget = AsyncMock(return_value=[None, None])
    client.get = AsyncMock(return_value=None)
    client.ping = AsyncMock(return_value=True)
    client.aclose = AsyncMock()
    client.pubsub = MagicMock()
    return client


@pytest.fixture
def mock_httpx_client() -> AsyncMock:
    """Cliente HTTP mockado para testes de RPC."""
    response = AsyncMock()
    response.json = AsyncMock(return_value={})
    response.status_code = 200
    client = AsyncMock()
    client.post = AsyncMock(return_value=response)
    client.aclose = AsyncMock()
    return client

