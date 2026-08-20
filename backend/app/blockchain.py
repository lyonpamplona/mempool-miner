"""Cliente ZMQ assíncrono para eventos publicados pelo Bitcoin Core."""

from __future__ import annotations

import asyncio
import binascii
import logging
from collections.abc import Awaitable, Callable
from uuid import uuid4

import zmq
import zmq.asyncio

from app.config import NodeConfig
from app.events import BlockNotice, RawTransactionNotice, ZmqSource, utc_now_iso

logger = logging.getLogger(__name__)

TransactionCallback = Callable[[RawTransactionNotice], None]
BlockCallback = Callable[[BlockNotice], Awaitable[None]]


class BitcoinZMQListener:
    """Encaminha transações e blocos do Bitcoin Core para a aplicação."""

    def __init__(
        self,
        config: NodeConfig,
        transaction_callback: TransactionCallback,
        block_callback: BlockCallback,
        context: zmq.asyncio.Context | None = None,
    ) -> None:
        """Configura uma origem explícita; cada nó usa seu próprio socket SUB."""
        self.config = config
        self.transaction_callback = transaction_callback
        self.block_callback = block_callback
        self.ctx = context or zmq.asyncio.Context()
        self._owns_context = context is None
        self.socket = self.ctx.socket(zmq.SUB)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.is_running = False
        self.source_session = uuid4().hex
        self.local_sequence = 0

    def _source(self, message: list[bytes]) -> ZmqSource:
        """Usa contador local monotônico para ordenação dos eventos ZMQ.

        O Bitcoin Core ZMQ ``rawtx`` envia apenas 2 frames (topic + body).
        O terceiro frame só existe em ``zmqpubsequence``, que é um publisher
        diferente — portanto, a sequência local é o único mecanismo de ordenação.

        Args:
            message: Lista de frames recebida do socket ZMQ.

        Returns:
            ``ZmqSource`` com sessão, sequência e timestamp.
        """
        self.local_sequence += 1
        return ZmqSource(
            session_id=self.source_session,
            sequence=self.local_sequence,
            observed_at=utc_now_iso(),
        )

    async def start(self) -> None:
        """Conecta ao publisher ZMQ e processa mensagens até o cancelamento.

        Subscreve os tópicos ``rawtx`` e ``hashblock``. Cada mensagem é
        encaminhada para o callback correspondente. O loop encerra quando:
        - ``asyncio.CancelledError`` é recebido (shutdown graceful).
        - ``zmq.ZMQError`` é levantado (falha de conexão).

        Raises:
            asyncio.CancelledError: Quando o listener é cancelado.
            zmq.ZMQError: Quando há falha de conexão com o Bitcoin Core.
        """
        zmq_url = self.config.zmq_url
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
                source = self._source(message)
                if topic == b"rawtx":
                    self.transaction_callback(
                        RawTransactionNotice(
                            node_id=self.config.node_id,
                            network=self.config.network,
                            realm_id=self.config.realm_id,
                            tx_hex=binascii.hexlify(body).decode("ascii"),
                            source=source,
                        )
                    )
                elif topic == b"hashblock":
                    # Falhar um bloco silenciosamente deixaria epoch e contador
                    # divergentes. A exceção encerra o ingestor para o supervisor
                    # reiniciá-lo e reconciliar o estado com o Bitcoin Core.
                    await self.block_callback(
                        BlockNotice(
                            node_id=self.config.node_id,
                            network=self.config.network,
                            realm_id=self.config.realm_id,
                            block_hash=binascii.hexlify(body).decode("ascii"),
                            source=source,
                        )
                    )
        except asyncio.CancelledError:
            logger.info("Listener ZMQ cancelado")
            raise
        except zmq.ZMQError:
            logger.exception("Falha no listener ZMQ")
            raise
        finally:
            self.socket.close()
            if self._owns_context:
                self.ctx.term()
            self.is_running = False

    def stop(self) -> None:
        """Solicita o encerramento do loop de leitura ZMQ.

        Seta ``is_running = False``, fazendo o loop em ``start()`` encerrar
        na próxima iteração. O socket e o contexto são liberados no ``finally``.
        """
        self.is_running = False
