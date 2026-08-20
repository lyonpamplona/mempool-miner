"""Testes de isolamento e configuração da arquitetura multi-rede."""

from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import app.ingestor as ingestor_module
import app.ingestor_healthcheck as health_module
import app.main as main_module
import pytest
from app.config import BitcoinNetwork, NodeConfig, validate_realm_id
from app.events import (
    BlockNotice,
    RawTransactionNotice,
    ZmqSource,
    event_envelope,
    utc_now_iso,
)
from app.ingestor import NodeIngestor
from app.main import ScoreSubmit
from app.storage import events_channel, leaderboard_key, mempool_count_key
from fastapi import HTTPException
from factories import create_mock_ingestor


def node_config(network: BitcoinNetwork = BitcoinNetwork.REGTEST) -> NodeConfig:
    """Cria uma origem isolada sem depender do ambiente do host."""
    realm_id = network.value
    node_ids = {
        BitcoinNetwork.REGTEST: "regtest-local",
        BitcoinNetwork.SIGNET: "signet-public",
        BitcoinNetwork.MAINNET: "mainnet-pruned",
    }
    return NodeConfig(
        node_id=node_ids[network],
        realm_id=realm_id,
        network=network,
        rpc_host=f"bitcoin-{realm_id}",
        rpc_port=18443,
        zmq_host=f"bitcoin-{realm_id}",
        zmq_port=28332,
        rpc_user="test",
        rpc_password="test",
    )


def test_main_alias_is_normalized() -> None:
    """A nomenclatura pública mainnet mapeia para a chain RPC main."""
    assert BitcoinNetwork.parse("main") is BitcoinNetwork.MAINNET
    assert BitcoinNetwork.MAINNET.rpc_chain == "main"


@pytest.mark.parametrize("realm_id", ["../../main", "MAIN NET", "{signet}", ""])
def test_realm_id_rejects_namespace_injection(realm_id: str) -> None:
    """IDs arbitrários não podem compor chaves Redis."""
    with pytest.raises(ValueError):
        validate_realm_id(realm_id)


def test_redis_namespaces_are_isolated() -> None:
    """Canal, contador e ranking não colidem entre Regtest e Signet."""
    for builder in (events_channel, mempool_count_key, leaderboard_key):
        assert builder("regtest") != builder("signet")


def test_node_config_rejects_cross_network_realm() -> None:
    """Uma configuração Signet não pode publicar no namespace Regtest."""
    with pytest.raises(ValueError, match="não pertence"):
        NodeConfig(
            node_id="bad-node",
            realm_id="regtest",
            network=BitcoinNetwork.SIGNET,
            rpc_host="bitcoin-signet",
            rpc_port=38332,
            zmq_host="bitcoin-signet",
            zmq_port=28332,
            rpc_user="test",
            rpc_password="test",
        )


def test_node_config_rejects_node_id_outside_catalog() -> None:
    """A API e o ingestor precisam concordar sobre a chave de heartbeat."""
    with pytest.raises(ValueError, match="diverge do catálogo"):
        NodeConfig(
            node_id="regtest-secondary",
            realm_id="regtest",
            network=BitcoinNetwork.REGTEST,
            rpc_host="bitcoin-regtest",
            rpc_port=18443,
            zmq_host="bitcoin-regtest",
            zmq_port=28332,
            rpc_user="test",
            rpc_password="test",
        )


@pytest.mark.parametrize(
    ("network", "expected_node_id"),
    [
        ("regtest", "regtest-local"),
        ("signet", "signet-public"),
        ("mainnet", "mainnet-pruned"),
    ],
)
def test_environment_uses_catalog_node_id(
    monkeypatch: pytest.MonkeyPatch,
    network: str,
    expected_node_id: str,
) -> None:
    """O default do ingestor deve ser observável pelo catálogo estático da API."""
    monkeypatch.setenv("BITCOIN_NETWORK", network)
    monkeypatch.setenv("REALM_ID", network)
    monkeypatch.setenv("RPC_USER", "test")
    monkeypatch.setenv("RPC_PASSWORD", "test")
    monkeypatch.delenv("NODE_ID", raising=False)

    assert NodeConfig.from_environment().node_id == expected_node_id


@pytest.mark.asyncio
async def test_score_uses_selected_realm(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pontuação Signet nunca é gravada no leaderboard Regtest."""
    zadd = AsyncMock(return_value=1)
    monkeypatch.setattr(main_module.redis_client, "zadd", zadd)
    monkeypatch.setattr(
        main_module,
        "network_snapshot",
        AsyncMock(return_value={"playable": True}),
    )

    result = await main_module.submit_score_for_realm(
        "signet", ScoreSubmit(username="Miner", score=7)
    )

    assert result["realm_id"] == "signet"
    zadd.assert_awaited_once_with(leaderboard_key("signet"), {"Miner": 7}, gt=True, ch=True)


@pytest.mark.asyncio
async def test_score_rejects_disabled_realm(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mainnet sem profile não aceita gravação de ranking."""
    monkeypatch.setattr(
        main_module,
        "network_snapshot",
        AsyncMock(return_value={"playable": False}),
    )
    with pytest.raises(HTTPException) as error:
        await main_module.submit_score_for_realm("mainnet", ScoreSubmit(username="Miner", score=7))
    assert error.value.status_code == 409


@pytest.mark.asyncio
async def test_network_catalog_marks_absent_mainnet_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A ausência do profile Mainnet não derruba nem oculta o catálogo."""
    get = AsyncMock(return_value=None)
    monkeypatch.setattr(main_module.redis_client, "get", get)

    snapshot = await main_module.network_snapshot("mainnet")

    assert snapshot["status"] == "disabled"
    assert snapshot["playable"] is False
    assert set(snapshot) == {
        "realm_id",
        "network",
        "display_name",
        "status",
        "playable",
        "initial_block_download",
        "verification_progress",
        "pruned",
    }


@pytest.mark.asyncio
async def test_live_pruned_node_is_playable(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pruning não é confundido com indisponibilidade ou IBD."""
    status = json.dumps(
        {
            "status": "ready",
            "playable": True,
            "initial_block_download": False,
            "pruned": True,
            "mempool_count": 3,
            "_runtime_token": "internal-only",
        }
    )

    async def fake_get(key: str):
        if key.endswith(":status"):
            return status
        if key.endswith(":mempool_count"):
            return "3"
        return None

    monkeypatch.setattr(main_module.redis_client, "get", fake_get)
    snapshot = await main_module.network_snapshot("mainnet")
    assert snapshot["status"] == "ready"
    assert snapshot["playable"] is True
    assert snapshot["pruned"] is True
    assert "_runtime_token" not in snapshot


def test_block_advances_only_its_ingestor_epoch() -> None:
    """A origem do notice permanece explícita até o runtime correto."""
    source = ZmqSource("session", 1, "2026-08-14T00:00:00+00:00")
    notice = BlockNotice(
        node_id="signet-test",
        network=BitcoinNetwork.SIGNET,
        realm_id="signet",
        block_hash="ab" * 32,
        source=source,
    )
    assert notice.realm_id == "signet"
    assert notice.network is BitcoinNetwork.SIGNET


@pytest.mark.asyncio
async def test_old_transaction_cannot_publish_after_new_block() -> None:
    """Uma resposta RPC atrasada não pode atravessar a barreira de epoch."""
    redis_client = MagicMock()
    redis_client.eval = AsyncMock(return_value=1)

    ingestor = create_mock_ingestor(
        redis_client=redis_client,
        epoch="epoch-antiga",
        lease_token="owner-a",
    )
    ingestor._increment_block_counter = AsyncMock()
    ingestor._generate_block_card = AsyncMock()
    ingestor.update_status = AsyncMock()

    metadata_started = asyncio.Event()
    release_metadata = asyncio.Event()

    async def delayed_metadata(_txid: str, _tx_hex: str | None = None) -> dict[str, object]:
        metadata_started.set()
        await release_metadata.wait()
        return {
            "word": "BITCOIN",
            "is_golden": False,
            "is_high_fee": False,
            "vsize": 100,
            "fee_rate_sat_vb": 1.0,
        }

    ingestor.engine.get_tx_metadata = delayed_metadata
    source = ZmqSource("session", 1, "2026-08-14T00:00:00+00:00")
    transaction = RawTransactionNotice(
        node_id="regtest-local",
        network=BitcoinNetwork.REGTEST,
        realm_id="regtest",
        tx_hex="00",
        source=source,
    )
    block = BlockNotice(
        node_id="regtest-local",
        network=BitcoinNetwork.REGTEST,
        realm_id="regtest",
        block_hash="ab" * 32,
        source=replace(source, sequence=2),
    )

    transaction_task = asyncio.create_task(
        ingestor.process_transaction("epoch-antiga", transaction)
    )
    await metadata_started.wait()
    await ingestor.handle_block(block)
    release_metadata.set()
    await transaction_task

    redis_client.eval.assert_awaited_once()
    commit_call = redis_client.eval.await_args
    assert commit_call.args[0] == ingestor_module.COMMIT_BLOCK_SCRIPT
    assert json.loads(commit_call.args[-1])["action"] == "block_mined"


@pytest.mark.asyncio
async def test_stale_lease_cannot_commit_transaction() -> None:
    """O antigo dono precisa parar quando o commit Redis recusa seu token."""
    redis_client = MagicMock()
    redis_client.eval = AsyncMock(return_value=[-1, 0])
    ingestor = create_mock_ingestor(
        redis_client=redis_client,
        epoch="epoch-a",
        lease_token="owner-antigo",
    )
    ingestor.engine.get_tx_metadata = AsyncMock(
        return_value={
            "word": "BITCOIN",
            "is_golden": False,
            "is_high_fee": False,
            "vsize": 100,
            "fee_rate_sat_vb": 1.0,
        }
    )
    ingestor.engine.get_mempool_size = AsyncMock(return_value=1)
    notice = RawTransactionNotice(
        node_id="regtest-local",
        network=BitcoinNetwork.REGTEST,
        realm_id="regtest",
        tx_hex="00",
        source=ZmqSource("session", 1, utc_now_iso()),
    )

    with pytest.raises(RuntimeError, match="Lease perdida"):
        await ingestor.process_transaction("epoch-a", notice)


@pytest.mark.asyncio
async def test_status_keeps_runtime_token_out_of_public_event() -> None:
    """O token de fencing fica apenas no snapshot Redis interno."""
    redis_client = MagicMock()
    redis_client.eval = AsyncMock(return_value=1)
    ingestor = create_mock_ingestor(
        redis_client=redis_client,
        lease_token="internal-token",
    )
    ingestor.status = "starting"
    ingestor.playable = False

    await ingestor.update_status(
        {
            "initialblockdownload": False,
            "verificationprogress": 1.0,
            "blocks": 100,
            "headers": 100,
            "bestblockhash": "ab" * 32,
        }
    )

    commit_call = redis_client.eval.await_args
    assert commit_call.args[0] == ingestor_module.COMMIT_STATUS_SCRIPT
    stored_snapshot = json.loads(commit_call.args[-2])
    public_event = json.loads(commit_call.args[-1])
    assert stored_snapshot["_runtime_token"] == "internal-token"
    assert "_runtime_token" not in public_event


@pytest.mark.asyncio
async def test_close_updates_status_and_releases_lease_atomically(tmp_path: Path) -> None:
    """Shutdown usa um único script compare/status/DEL, sem janela de takeover."""
    redis_client = MagicMock()
    redis_client.eval = AsyncMock(return_value=1)
    redis_client.aclose = AsyncMock()
    ingestor = create_mock_ingestor(
        redis_client=redis_client,
        lease_token="owner-a",
    )
    ingestor.listener = MagicMock()
    ingestor.tasks = set()
    ingestor.engine.close = AsyncMock()
    ingestor.token_file = tmp_path / "runtime-token"
    ingestor.token_file.write_text("owner-a", encoding="utf-8")

    await ingestor.close()

    redis_client.eval.assert_awaited_once()
    assert redis_client.eval.await_args.args[0] == ingestor_module.STOP_AND_RELEASE_SCRIPT
    assert not ingestor.token_file.exists()


@pytest.mark.asyncio
async def test_old_owner_does_not_remove_successor_token_file(tmp_path: Path) -> None:
    """O teardown perdedor não apaga o token local escrito pelo sucessor."""
    redis_client = MagicMock()
    redis_client.eval = AsyncMock(return_value=0)
    redis_client.aclose = AsyncMock()
    ingestor = create_mock_ingestor(
        redis_client=redis_client,
        lease_token="owner-a",
    )
    ingestor.listener = MagicMock()
    ingestor.tasks = set()
    ingestor.engine.close = AsyncMock()
    ingestor.token_file = tmp_path / "runtime-token"
    # Token do sucessor já está no arquivo — o antigo dono não deve apagá-lo.
    ingestor.token_file.write_text("owner-novo", encoding="utf-8")

    await ingestor.close()

    assert ingestor.token_file.read_text(encoding="utf-8") == "owner-novo"


@pytest.mark.asyncio
async def test_healthcheck_rejects_heartbeat_from_other_instance(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Um contêiner não pode ficar healthy usando o heartbeat do sucessor."""
    token_file = tmp_path / "runtime-token"
    token_file.write_text("owner-a", encoding="utf-8")
    monkeypatch.setenv("NODE_ID", "regtest-local")
    monkeypatch.setenv("REALM_ID", "regtest")
    monkeypatch.setenv("INGESTOR_TOKEN_FILE", str(token_file))
    client = MagicMock()
    client.mget = AsyncMock(
        return_value=[
            json.dumps(
                {
                    "node_id": "regtest-local",
                    "realm_id": "regtest",
                    "status": "ready",
                    "_runtime_token": "owner-b",
                    "updated_at": utc_now_iso(),
                }
            ),
            "owner-b",
        ]
    )
    client.aclose = AsyncMock()
    monkeypatch.setattr(health_module.redis, "from_url", MagicMock(return_value=client))

    with pytest.raises(RuntimeError, match="outra instância"):
        await health_module.check()


def test_event_envelope_carries_source_and_realm() -> None:
    """Origem e realm ficam disponíveis para dedupe e filtragem do cliente."""
    source = ZmqSource("session-a", 42, "2026-08-14T00:00:00+00:00")
    event = event_envelope(
        action="transaction_received",
        node_id="regtest-test",
        network=BitcoinNetwork.REGTEST,
        realm_id="regtest",
        source=source,
        epoch="epoch-a",
    )
    assert event["event_id"] == "regtest-test:session-a:transaction_received:42"
    assert event["realm_id"] == "regtest"
    assert event["source_sequence"] == 42


@pytest.mark.asyncio
async def test_full_queue_drops_without_blocking() -> None:
    """Rawtx excedente é descartada em vez de bloquear o socket ZMQ."""
    config = replace(node_config(), queue_max_size=1)
    ingestor = NodeIngestor(config, AsyncMock())
    source = ZmqSource("session", 1, "2026-08-14T00:00:00+00:00")
    notice = RawTransactionNotice(
        node_id=config.node_id,
        network=config.network,
        realm_id=config.realm_id,
        tx_hex="00",
        source=source,
    )
    ingestor.enqueue_transaction(notice)
    ingestor.enqueue_transaction(notice)
    assert ingestor.queue.qsize() == 1
    assert ingestor.dropped_transactions == 1
    ingestor.listener.socket.close(0)
    ingestor.listener.ctx.term()
    await ingestor.engine.close()
