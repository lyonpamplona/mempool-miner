"""Cliente ZMQ assíncrono para eventos publicados pelo Bitcoin Core."""

from __future__ import annotations

import asyncio
import binascii
import logging
import os
from collections.abc import Awaitable, Callable

import zmq
import zmq.asyncio

logger = logging.getLogger(__name__)

BlockCallback = Callable[[str], Awaitable[None]]


class BitcoinZMQListener:
    """Encaminha transações e blocos do Bitcoin Core para a aplicação."""

    def __init__(self, tx_queue: asyncio.Queue[str], block_callback: BlockCallback) -> None:
        """Configura o endereço ZMQ, a fila de transações e o callback de bloco."""
        self.zmq_host = os.getenv("ZMQ_HOST", os.getenv("RPC_HOST", "bitcoind"))
        self.zmq_port = os.getenv("ZMQ_PORT", "28332")
        self.tx_queue = tx_queue
        self.block_callback = block_callback
        self.ctx = zmq.asyncio.Context()
        self.socket = self.ctx.socket(zmq.SUB)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.is_running = False

    async def start(self) -> None:
        """Conecta ao publisher e processa mensagens até o cancelamento."""
        zmq_url = f"tcp://{self.zmq_host}:{self.zmq_port}"
        self.socket.connect(zmq_url)
        self.socket.setsockopt(zmq.SUBSCRIBE, b"rawtx")
        self.socket.setsockopt(zmq.SUBSCRIBE, b"hashblock")
        self.is_running = True
        logger.info("Listener ZMQ conectado em %s", zmq_url)

        try:
            while self.is_running:
                message = await self.socket.recv_multipart()
                if len(message) < 2:
                    logger.warning("Mensagem ZMQ ignorada: multipart incompleto")
                    continue

                topic = message[0]
                body = message[1]
                if topic == b"rawtx":
                    await self.tx_queue.put(binascii.hexlify(body).decode("ascii"))
                elif topic == b"hashblock":
                    try:
                        await self.block_callback(binascii.hexlify(body).decode("ascii"))
                    except Exception:
                        logger.exception("Falha ao processar evento de novo bloco")
        except asyncio.CancelledError:
            logger.info("Listener ZMQ cancelado")
            raise
        except zmq.ZMQError:
            logger.exception("Falha no listener ZMQ")
            raise
        finally:
            self.socket.close()
            self.ctx.term()
            self.is_running = False

    def stop(self) -> None:
        """Solicita o encerramento do loop de leitura ZMQ."""
        self.is_running = False
