"""Testes dos contratos expostos pela API."""

import os
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

os.environ.setdefault("RPC_USER", "test_user")
os.environ.setdefault("RPC_PASSWORD", "test_password")

import app.main as main_module  # noqa: E402
from app.main import MAX_SCORE, ScoreSubmit, app, engine  # noqa: E402


def test_score_submit_normalizes_username() -> None:
    """Espaços externos são removidos de um nickname válido."""
    payload = ScoreSubmit(username=" abcdefghijkl ", score=42)
    assert payload.username == "abcdefghijkl"


@pytest.mark.parametrize("username", ["", "nome<script>", "nome com espaço"])
def test_score_submit_rejects_unsafe_username(username: str) -> None:
    """Nicknames vazios ou com separadores inseguros são recusados."""
    with pytest.raises(ValidationError):
        ScoreSubmit(username=username, score=42)


@pytest.mark.parametrize("score", [-1, MAX_SCORE + 1])
def test_score_submit_rejects_out_of_range_score(score: int) -> None:
    """A API limita a pontuação ao intervalo documentado."""
    with pytest.raises(ValidationError):
        ScoreSubmit(username="Miner", score=score)


def test_expected_routes_are_registered() -> None:
    """Healthcheck, leaderboard e WebSocket devem permanecer publicados."""
    paths = {route.path for route in app.routes}
    assert {"/api/health", "/api/leaderboard", "/ws/game"} <= paths


@pytest.mark.asyncio
async def test_submit_score_reports_an_existing_record_update(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A resposta usa CH para reconhecer a alteração de um membro existente."""
    zadd = AsyncMock(return_value=1)
    monkeypatch.setattr(main_module.redis_client, "zadd", zadd)

    result = await main_module.submit_score(ScoreSubmit(username="Miner", score=43))

    assert result == {"status": "success", "updated": True}
    zadd.assert_awaited_once_with(
        main_module.LEADERBOARD_KEY,
        {"Miner": 43},
        gt=True,
        ch=True,
    )


@pytest.fixture(scope="session", autouse=True)
async def close_global_engine() -> None:
    """Fecha o cliente HTTP global ao término da suíte."""
    yield
    await engine.close()
