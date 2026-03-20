"""Integration tests for MiniMax bot with the MiniMax API.

These tests require a valid MINIMAX_API_KEY environment variable.
Skip with: pytest -m "not integration"
"""

from __future__ import annotations

import os

import pytest

from xiaogpt.bot.minimax_bot import MiniMaxBot

MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")

pytestmark = pytest.mark.skipif(
    not MINIMAX_API_KEY, reason="MINIMAX_API_KEY not set"
)


@pytest.fixture
def minimax_bot():
    return MiniMaxBot(minimax_api_key=MINIMAX_API_KEY)


class TestMiniMaxIntegration:
    """Integration tests that hit the real MiniMax API."""

    @pytest.mark.asyncio
    async def test_ask_real_api(self, minimax_bot):
        """Test a real API call to MiniMax."""
        response = await minimax_bot.ask("Say hello in one word.")
        assert response  # non-empty response
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_ask_stream_real_api(self, minimax_bot):
        """Test streaming from the real MiniMax API."""
        sentences = []
        async for sentence in minimax_bot.ask_stream("Say hi in one word."):
            sentences.append(sentence)
        full_response = "".join(sentences)
        assert full_response  # non-empty response
        assert len(full_response) > 0

    @pytest.mark.asyncio
    async def test_conversation_history(self, minimax_bot):
        """Test that conversation history is maintained across calls."""
        await minimax_bot.ask("My name is TestBot.")
        assert minimax_bot.has_history()
        response = await minimax_bot.ask("What is my name?")
        assert response
        assert len(minimax_bot.history) == 2
