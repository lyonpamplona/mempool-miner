"""Testes unitários do motor de metadados."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.config import BitcoinNetwork, NodeConfig
from app.engine import GameEngine


@pytest.mark.asyncio
async def test_tx_to_word_is_deterministic() -> None:
    """O mesmo TXID deve produzir sempre a primeira palavra BIP39 esperada."""
    config = NodeConfig(
        node_id="regtest-local",
        realm_id="regtest",
        network=BitcoinNetwork.REGTEST,
        rpc_host="localhost",
        rpc_port=18443,
        zmq_host="localhost",
        zmq_port=28332,
        rpc_user="test",
        rpc_password="test",
    )
    engine = GameEngine(config)
    assert engine.tx_to_word("0" * 64) == "ABANDON"
    await engine.close()


@pytest.mark.asyncio
async def test_tx_to_word_handles_invalid_hash() -> None:
    """Hashes inválidos usam o fallback documentado."""
    config = NodeConfig(
        node_id="regtest-local",
        realm_id="regtest",
        network=BitcoinNetwork.REGTEST,
        rpc_host="localhost",
        rpc_port=18443,
        zmq_host="localhost",
        zmq_port=28332,
        rpc_user="test",
        rpc_password="test",
    )
    engine = GameEngine(config)
    assert engine.tx_to_word("invalido") == "BITCOIN"
    await engine.close()


@pytest.mark.asyncio
async def test_metadata_uses_fee_rate_in_sat_vb(monkeypatch: pytest.MonkeyPatch) -> None:
    """A classificação de taxa considera sats/vB, não a taxa absoluta."""
    config = NodeConfig(
        node_id="regtest-local",
        realm_id="regtest",
        network=BitcoinNetwork.REGTEST,
        rpc_host="localhost",
        rpc_port=18443,
        zmq_host="localhost",
        zmq_port=28332,
        rpc_user="test",
        rpc_password="test",
    )
    engine = GameEngine(config)

    async def fake_rpc_call(method: str, params: list[str]) -> dict:
        """Simula a resposta RPC usada para calcular a taxa em sats/vB."""
        assert method == "getmempoolentry"
        assert len(params) == 1
        return {"vsize": 250, "fees": {"base": 0.00005}}

    monkeypatch.setattr(engine, "_rpc_call", fake_rpc_call)
    metadata = await engine.get_tx_metadata("1" * 64)

    assert metadata["fee_rate_sat_vb"] == 20.0
    assert metadata["is_high_fee"] is True
    await engine.close()


@pytest.mark.asyncio
async def test_engine_rejects_rpc_from_another_chain(monkeypatch: pytest.MonkeyPatch) -> None:
    """Um ingestor Regtest não pode aceitar por engano um RPC Signet."""
    config = NodeConfig(
        node_id="regtest-local",
        realm_id="regtest",
        network=BitcoinNetwork.REGTEST,
        rpc_host="bitcoin-regtest",
        rpc_port=18443,
        zmq_host="bitcoin-regtest",
        zmq_port=28332,
        rpc_user="test",
        rpc_password="test",
    )
    engine = GameEngine(config)

    async def fake_info() -> dict[str, str]:
        return {"chain": "signet"}

    monkeypatch.setattr(engine, "get_blockchain_info", fake_info)
    with pytest.raises(RuntimeError, match="Chain RPC divergente"):
        await engine.validate_declared_network()
    await engine.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("document", [[], None, "invalid"])
async def test_rpc_rejects_non_object_json(
    monkeypatch: pytest.MonkeyPatch,
    node_config: NodeConfig,
    document: object,
) -> None:
    """JSON válido, mas fora do envelope RPC, não pode derrubar o ingestor."""
    engine = GameEngine(node_config)
    response = MagicMock()
    response.json.return_value = document
    monkeypatch.setattr(engine.http_client, "post", AsyncMock(return_value=response))

    assert await engine._rpc_call("getblockchaininfo", []) is None
    await engine.close()
