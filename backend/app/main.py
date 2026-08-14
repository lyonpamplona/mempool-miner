"""API FastAPI do Mempool Miner, com Redis, WebSocket e ingestão ZMQ."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
from contextlib import asynccontextmanager
from typing import Annotated, Any

import redis.asyncio as redis
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, BeforeValidator, Field

from app.blockchain import BitcoinZMQListener
from app.engine import GameEngine

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

CHANNEL_NAME = "game_events"
LEADERBOARD_KEY = "global_leaderboard"
MEMPOOL_COUNT_KEY = "mempool_count"
MAX_SCORE = 2_147_483_647
QUEUE_MAX_SIZE = int(os.getenv("TX_QUEUE_MAX_SIZE", "5000"))
PROCESS_INTERVAL_SECONDS = float(os.getenv("TX_PROCESS_INTERVAL_SECONDS", "1.0"))

tx_queue: asyncio.Queue[str] = asyncio.Queue(maxsize=QUEUE_MAX_SIZE)
engine = GameEngine()
redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
redis_client = redis.from_url(redis_url, decode_responses=True)


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


class ScoreSubmit(BaseModel):
    """Representa uma atualização de pontuação enviada pelo cliente."""

    username: Username
    score: int = Field(ge=0, le=MAX_SCORE)


async def process_tx_queue() -> None:
    """Consome a fila ZMQ com cadência configurável e publica eventos no Redis."""
    while True:
        tx_hex = await tx_queue.get()
        try:
            txid = (
                hashlib.sha256(hashlib.sha256(bytes.fromhex(tx_hex)).digest()).digest()[::-1].hex()
            )
            metadata = await engine.get_tx_metadata(txid)
            observed_count = await redis_client.incr(MEMPOOL_COUNT_KEY)
            payload = {
                "action": "transaction_received",
                "mempool_count": int(observed_count),
                "word": metadata["word"],
                "tx_stub": txid[:8],
                "is_golden": metadata["is_golden"],
                "is_high_fee": metadata["is_high_fee"],
                "vsize": metadata["vsize"],
                "fee_rate_sat_vb": metadata["fee_rate_sat_vb"],
            }
            await redis_client.publish(CHANNEL_NAME, json.dumps(payload))
        except (ValueError, TypeError, redis.RedisError):
            logger.exception("Falha ao processar transação recebida via ZMQ")
        finally:
            tx_queue.task_done()

        if PROCESS_INTERVAL_SECONDS > 0:
            await asyncio.sleep(PROCESS_INTERVAL_SECONDS)


async def handle_block(block_hash: str) -> None:
    """Reinicia a rodada observada e anuncia um novo bloco aos clientes."""
    mempool_size = await engine.get_mempool_size()
    current_count = mempool_size if mempool_size is not None else 0
    await redis_client.set(MEMPOOL_COUNT_KEY, current_count)
    payload = {
        "action": "block_mined",
        "block_hash": block_hash,
        "mempool_count": current_count,
    }
    await redis_client.publish(CHANNEL_NAME, json.dumps(payload))


zmq_listener = BitcoinZMQListener(tx_queue=tx_queue, block_callback=handle_block)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Inicializa dependências e encerra tarefas assíncronas de forma ordenada."""
    await redis_client.ping()
    initial_size = await engine.get_mempool_size()
    await redis_client.set(MEMPOOL_COUNT_KEY, initial_size or 0)

    task_zmq = asyncio.create_task(zmq_listener.start(), name="bitcoin-zmq-listener")
    task_queue = asyncio.create_task(process_tx_queue(), name="transaction-processor")
    tasks = (task_zmq, task_queue)
    try:
        yield
    finally:
        zmq_listener.stop()
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await engine.close()
        await redis_client.aclose()


app = FastAPI(
    title="Mempool Miner API",
    summary="Eventos Bitcoin transformados em partidas de caça-palavras.",
    version="1.0.0",
    lifespan=lifespan,
)

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:8010,http://127.0.0.1:8010",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health", tags=["Operação"])
async def healthcheck() -> dict[str, str]:
    """Confirma que a API consegue se comunicar com o Redis."""
    await redis_client.ping()
    return {"status": "ok"}


@app.post("/api/leaderboard", tags=["Leaderboard"])
async def submit_score(data: ScoreSubmit) -> dict[str, str | bool]:
    """Mantém atomicamente a maior pontuação conhecida de um jogador."""
    updated = await redis_client.zadd(
        LEADERBOARD_KEY,
        {data.username: data.score},
        gt=True,
        ch=True,
    )
    return {"status": "success", "updated": bool(updated)}


@app.get("/api/leaderboard", tags=["Leaderboard"])
async def get_leaderboard() -> dict[str, list[dict[str, str | int]]]:
    """Retorna os dez jogadores com maior pontuação."""
    top_miners = await redis_client.zrevrange(
        LEADERBOARD_KEY,
        0,
        9,
        withscores=True,
    )
    leaderboard = [{"username": username, "score": int(score)} for username, score in top_miners]
    return {"leaderboard": leaderboard}


async def ws_sender(websocket: WebSocket, pubsub: redis.client.PubSub) -> None:
    """Repassa mensagens Redis Pub/Sub para um cliente WebSocket."""
    async for message in pubsub.listen():
        if message["type"] == "message":
            await websocket.send_text(message["data"])


async def ws_receiver(websocket: WebSocket) -> None:
    """Mantém a conexão aberta e detecta o desligamento do navegador."""
    while True:
        message: dict[str, Any] = await websocket.receive()
        if message["type"] == "websocket.disconnect":
            return


@app.websocket("/ws/game")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Entrega o estado inicial e os eventos ao vivo de transação e bloco."""
    await websocket.accept()
    pubsub = redis_client.pubsub()
    sender_task: asyncio.Task[None] | None = None
    receiver_task: asyncio.Task[None] | None = None

    try:
        await pubsub.subscribe(CHANNEL_NAME)
        current_count = await redis_client.get(MEMPOOL_COUNT_KEY)
        await websocket.send_text(
            json.dumps(
                {
                    "action": "game_start",
                    "network": engine.network,
                    "game_mode": engine.game_mode,
                    "mempool_count": int(current_count or 0),
                }
            )
        )

        sender_task = asyncio.create_task(ws_sender(websocket, pubsub))
        receiver_task = asyncio.create_task(ws_receiver(websocket))
        done, pending = await asyncio.wait(
            {sender_task, receiver_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        for task in done:
            if task.cancelled():
                continue
            error = task.exception()
            if error:
                logger.debug("Conexão WebSocket encerrada: %s", error)
    finally:
        for task in (sender_task, receiver_task):
            if task and not task.done():
                task.cancel()
        await pubsub.unsubscribe(CHANNEL_NAME)
        await pubsub.aclose()
