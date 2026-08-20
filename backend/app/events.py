"""Contratos internos e públicos dos eventos Bitcoin multi-rede."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.config import BitcoinNetwork


def utc_now_iso() -> str:
    """Retorna um timestamp UTC serializável e explícito.

    Returns:
        String ISO 8601 com timezone (ex: ``2026-08-15T10:30:00+00:00``).
    """
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True, slots=True)
class ZmqSource:
    """Identifica uma observação dentro de uma sessão ZMQ."""

    session_id: str
    sequence: int
    observed_at: str


@dataclass(frozen=True, slots=True)
class RawTransactionNotice:
    """Transação crua recebida de um nó específico."""

    node_id: str
    network: BitcoinNetwork
    realm_id: str
    tx_hex: str
    source: ZmqSource


@dataclass(frozen=True, slots=True)
class BlockNotice:
    """Bloco recebido de um nó específico."""

    node_id: str
    network: BitcoinNetwork
    realm_id: str
    block_hash: str
    source: ZmqSource


def event_envelope(
    *,
    action: str,
    node_id: str,
    network: BitcoinNetwork,
    realm_id: str,
    source: ZmqSource | None = None,
    epoch: str | None = None,
) -> dict[str, Any]:
    """Cria os campos comuns obrigatórios do protocolo WebSocket v2.

    Gera ``event_id`` determinístico a partir de ``node_id``, ``session_id``,
    ``action`` e ``sequence``. Quando ``source`` é None, usa UUID aleatório.

    Args:
        action: Tipo do evento (ex: ``transaction``, ``block_mined``).
        node_id: Identificador do nó de origem.
        network: Rede Bitcoin (regtest, signet, mainnet).
        realm_id: Realm do evento.
        source: Fonte ZMQ (session, sequence, timestamp). Se None, usa UUID.
        epoch: Hash do melhor bloco no momento da observação.

    Returns:
        Dict com campos do envelope (schema_version, event_id, action, etc.).
    """
    if source:
        event_id = f"{node_id}:{source.session_id}:{action}:{source.sequence}"
        observed_at = source.observed_at
        source_session = source.session_id
        source_sequence = source.sequence
    else:
        event_id = f"{node_id}:{uuid4().hex}"
        observed_at = utc_now_iso()
        source_session = None
        source_sequence = None
    return {
        "schema_version": 2,
        "event_id": event_id,
        "action": action,
        "node_id": node_id,
        "network": network.value,
        "chain": network.rpc_chain,
        "realm_id": realm_id,
        "observed_at": observed_at,
        "source_session": source_session,
        "source_sequence": source_sequence,
        "epoch": epoch,
    }
