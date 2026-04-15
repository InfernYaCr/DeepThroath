from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.red_team.runner import create_anthropic_callback, run_red_team


@pytest.fixture(autouse=True)
def set_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


def test_create_anthropic_callback_returns_callable():
    with patch("anthropic.Anthropic"):
        cb = create_anthropic_callback("claude-3-5-sonnet-20241022", "You are helpful.")
    assert callable(cb)


def test_anthropic_callback_calls_api():
    import asyncio
    from deepteam.test_case import RTTurn
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Safe response")]
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    with patch("src.red_team.runner.AsyncAnthropic", return_value=mock_client):
        cb = create_anthropic_callback("claude-3-5-sonnet-20241022", "You are helpful.")
        result = asyncio.run(cb("Hello"))

    assert isinstance(result, RTTurn)
    assert result.content == "Safe response"
    assert result.role == "assistant"
    mock_client.messages.create.assert_called_once()


def test_run_red_team_returns_risk_assessment():
    mock_risk = MagicMock()
    mock_callback = MagicMock(return_value=MagicMock())

    with (
        patch("deepteam.red_team", return_value=mock_risk),
        patch("src.red_team.runner.build_attacks", return_value=[MagicMock()]),
        patch("src.red_team.runner.build_vulnerabilities", return_value=[MagicMock()]),
    ):
        result = run_red_team(mock_callback, attacks_per_vulnerability_type=1)

    assert result is mock_risk
