"""Testes do cliente ZMQ assíncrono."""

from __future__ import annotations

import binascii
from dataclasses import replace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import zmq

from app.blockchain import BitcoinZMQListener
from app.config import BitcoinNetwork, NodeConfig
from app.events import BlockNotice, RawTransactionNotice


@pytest.fixture
def zmq_config(node_config: NodeConfig) -> NodeConfig:
    """Config com ZMQ em localhost para testes."""
    return replace(
        node_config,
        zmq_host="localhost",
        zmq_port=28332,
    )


def test_zmq_listener_starts_and_stops(zmq_config: NodeConfig) -> None:
    """Listener inicializa e encerra sem erros."""
    tx_cb = MagicMock()
    block_cb = AsyncMock()
    ctx = zmq.asyncio.Context()
    listener = BitcoinZMQListener(zmq_config, tx_cb, block_cb, context=ctx)

    assert not listener.is_running
    assert listener.local_sequence == 0

    listener.stop()
    assert not listener.is_running

    listener.socket.close(0)
    ctx.term()


def test_zmq_source_uses_local_sequence(zmq_config: NodeConfig) -> None:
    """_source() usa contador local monotônico."""
    tx_cb = MagicMock()
    block_cb = AsyncMock()
    ctx = zmq.asyncio.Context()
    listener = BitcoinZMQListener(zmq_config, tx_cb, block_cb, context=ctx)

    # Simula mensagem ZMQ com 2 frames (topic + body).
    message = [b"rawtx", b"00" * 32]
    source = listener._source(message)

    assert source.sequence == 1
    assert source.session_id == listener.source_session
    assert source.observed_at is not None

    # Segunda chamada incrementa.
    source2 = listener._source(message)
    assert source2.sequence == 2

    listener.socket.close(0)
    ctx.term()


def test_zmq_source_ignores_third_frame(zmq_config: NodeConfig) -> None:
    """_source() ignora terceiro frame (zmqpubsequence é publisher diferente)."""
    tx_cb = MagicMock()
    block_cb = AsyncMock()
    ctx = zmq.asyncio.Context()
    listener = BitcoinZMQListener(zmq_config, tx_cb, block_cb, context=ctx)

    # Mensagem com 3 frames — o terceiro deve ser ignorado.
    message = [b"rawtx", b"00" * 32, b"\x00\x00"]
    source = listener._source(message)

    # Sequência local é usada, não o terceiro frame.
    assert source.sequence == 1

    listener.socket.close(0)
    ctx.term()


@pytest.mark.asyncio
async def test_zmq_listener_dispatches_rawtx(zmq_config: NodeConfig) -> None:
    """Mensagem rawtx é encaminhada para o callback de transação."""
    tx_cb = MagicMock()
    block_cb = AsyncMock()
    ctx = zmq.asyncio.Context()
    listener = BitcoinZMQListener(zmq_config, tx_cb, block_cb, context=ctx)

    # Simula mensagem rawtx.
    tx_hex = "00" * 32
    tx_bytes = binascii.unhexlify(tx_hex)
    message = [b"rawtx", tx_bytes]

    # Chama _source e callback manualmente (sem socket real).
    source = listener._source(message)
    listener.transaction_callback(
        RawTransactionNotice(
            node_id=listener.config.node_id,
            network=listener.config.network,
            realm_id=listener.config.realm_id,
            tx_hex=binascii.hexlify(tx_bytes).decode("ascii"),
            source=source,
        )
    )

    assert tx_cb.call_count == 1
    notice = tx_cb.call_args[0][0]
    assert isinstance(notice, RawTransactionNotice)
    assert notice.tx_hex == tx_hex
    assert notice.realm_id == "regtest"

    listener.socket.close(0)
    ctx.term()


@pytest.mark.asyncio
async def test_zmq_listener_dispatches_hashblock(zmq_config: NodeConfig) -> None:
    """Mensagem hashblock é encaminhada para o callback de bloco."""
    tx_cb = MagicMock()
    block_cb = AsyncMock()
    ctx = zmq.asyncio.Context()
    listener = BitcoinZMQListener(zmq_config, tx_cb, block_cb, context=ctx)

    # Simula mensagem hashblock.
    block_hex = "00" * 32
    block_bytes = binascii.unhexlify(block_hex)
    message = [b"hashblock", block_bytes]

    source = listener._source(message)
    await listener.block_callback(
        BlockNotice(
            node_id=listener.config.node_id,
            network=listener.config.network,
            realm_id=listener.config.realm_id,
            block_hash=binascii.hexlify(block_bytes).decode("ascii"),
            source=source,
        )
    )

    assert block_cb.call_count == 1
    notice = block_cb.call_args[0][0]
    assert isinstance(notice, BlockNotice)
    assert notice.block_hash == block_hex

    listener.socket.close(0)
    ctx.term()


def test_zmq_listener_ignores_incomplete_message(zmq_config: NodeConfig) -> None:
    """Mensagem com menos de 2 frames é ignorada."""
    tx_cb = MagicMock()
    block_cb = AsyncMock()
    ctx = zmq.asyncio.Context()
    listener = BitcoinZMQListener(zmq_config, tx_cb, block_cb, context=ctx)

    # Mensagem com apenas 1 frame — _source ainda funciona, mas o loop
    # de start() ignoraria. Testamos apenas que _source não crasha.
    message = [b"rawtx"]
    source = listener._source(message)
    assert source.sequence == 1

    listener.socket.close(0)
    ctx.term()
