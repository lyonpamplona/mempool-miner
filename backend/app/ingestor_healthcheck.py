"""Healthcheck do contêiner de ingestão baseado no heartbeat do Redis."""

from __future__ import annotations

import asyncio
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import redis.asyncio as redis

from app.config import validate_realm_id
from app.storage import ingestor_lease_key, node_status_key

MAX_HEARTBEAT_AGE_SECONDS = 45
HEALTHY_STATUSES = {"ready", "syncing"}


async def check() -> None:
    """Falha se o heartbeat estiver ausente, antigo ou fora do contrato.

    Verificações:
    1. Token local existe e não está vazio.
    2. Heartbeat existe no Redis e pertence ao mesmo node/realm.
    3. Timestamp do heartbeat tem timezone e não está expirado (45s).
    4. Lease token bate com o token local.
    5. Status é ``ready`` ou ``syncing``.

    Raises:
        RuntimeError: Se qualquer verificação falhar.
    """
    node_id = validate_realm_id(os.environ["NODE_ID"])
    realm_id = validate_realm_id(os.environ["REALM_ID"])
    token_file = Path(os.getenv("INGESTOR_TOKEN_FILE", "/tmp/mempool-miner-ingestor-token"))
    try:
        expected_token = token_file.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        raise RuntimeError("token local ausente")
    if not expected_token:
        raise RuntimeError("token local vazio")
    client = redis.from_url(
        os.getenv("REDIS_URL", "redis://redis:6379"),
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )
    try:
        raw_snapshot, active_token = await client.mget(
            node_status_key(node_id),
            ingestor_lease_key(realm_id),
        )
        if not raw_snapshot:
            raise RuntimeError("heartbeat ausente")
        snapshot = json.loads(raw_snapshot)
        updated_at = datetime.fromisoformat(snapshot["updated_at"])
        if updated_at.tzinfo is None:
            raise RuntimeError("heartbeat sem timezone")
        age = (datetime.now(UTC) - updated_at.astimezone(UTC)).total_seconds()
        if snapshot.get("node_id") != node_id or snapshot.get("realm_id") != realm_id:
            raise RuntimeError("heartbeat pertence a outra origem")
        if active_token != expected_token or snapshot.get("_runtime_token") != expected_token:
            raise RuntimeError("lease pertence a outra instância")
        if snapshot.get("status") not in HEALTHY_STATUSES:
            raise RuntimeError("ingestor não está pronto nem sincronizando")
        if age < 0 or age > MAX_HEARTBEAT_AGE_SECONDS:
            raise RuntimeError("heartbeat expirado")
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(check())
