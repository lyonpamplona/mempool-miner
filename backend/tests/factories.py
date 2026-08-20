"""Factories explícitas para testes que não dependem do sistema de fixtures."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.config import BitcoinNetwork, NodeConfig
from app.ingestor import NodeIngestor


def create_mock_ingestor(
    config: NodeConfig | None = None,
    redis_client: MagicMock | None = None,
    epoch: str = "test-epoch",
    playable: bool = True,
    lease_token: str = "test-token",
    mempool_size: int | None = 0,
) -> NodeIngestor:
    """Cria um ingestor isolado sem abrir RPC, Redis ou socket ZMQ."""
    if config is None:
        config = NodeConfig(
            node_id="regtest-local",
            realm_id="regtest",
            network=BitcoinNetwork.REGTEST,
            rpc_host="localhost",
            rpc_port=18443,
            zmq_host="localhost",
            zmq_port=28332,
            rpc_user="test_user",
            rpc_password="test_password",
        )

    ingestor = object.__new__(NodeIngestor)
    ingestor.config = config
    ingestor.redis = redis_client or MagicMock()
    if redis_client is None:
        ingestor.redis.eval = AsyncMock(return_value=1)
    ingestor.queue = asyncio.Queue()
    ingestor.epoch = epoch
    ingestor.playable = playable
    ingestor.epoch_lock = asyncio.Lock()
    ingestor.lease_key = f"lease:{config.realm_id}"
    ingestor.lease_token = lease_token
    ingestor.engine = MagicMock()
    ingestor.engine.get_mempool_size = AsyncMock(return_value=mempool_size)
    ingestor.dropped_transactions = 0
    ingestor.status = "ready"
    ingestor.last_info = {}
    return ingestor
