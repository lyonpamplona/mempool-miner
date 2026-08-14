"""Testes unitários do motor de metadados."""

import os

import pytest

os.environ.setdefault("RPC_USER", "test_user")
os.environ.setdefault("RPC_PASSWORD", "test_password")

from app.engine import GameEngine  # noqa: E402


@pytest.mark.asyncio
async def test_tx_to_word_is_deterministic() -> None:
    """O mesmo TXID deve produzir sempre a primeira palavra BIP39 esperada."""
    engine = GameEngine()
    assert engine.tx_to_word("0" * 64) == "ABANDON"
    await engine.close()


@pytest.mark.asyncio
async def test_tx_to_word_handles_invalid_hash() -> None:
    """Hashes inválidos usam o fallback documentado."""
    engine = GameEngine()
    assert engine.tx_to_word("invalido") == "BITCOIN"
    await engine.close()


@pytest.mark.asyncio
async def test_metadata_uses_fee_rate_in_sat_vb(monkeypatch: pytest.MonkeyPatch) -> None:
    """A classificação de taxa considera sats/vB, não a taxa absoluta."""
    engine = GameEngine()

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
