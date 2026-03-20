"""Unit tests for MiniMax bot."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from xiaogpt.bot.minimax_bot import MiniMaxBot


class TestMiniMaxBotInit:
    """Test MiniMaxBot initialization."""

    def test_name(self):
        assert MiniMaxBot.name == "MiniMax"

    def test_default_options(self):
        assert MiniMaxBot.default_options == {"model": "MiniMax-M1"}

    def test_init_defaults(self):
        bot = MiniMaxBot(minimax_api_key="test-key")
        assert bot.minimax_api_key == "test-key"
        assert bot.api_base == "https://api.minimax.io/v1"
        assert bot.history == []

    def test_init_custom_api_base(self):
        bot = MiniMaxBot(
            minimax_api_key="test-key",
            api_base="https://custom.api.com/v1",
        )
        assert bot.api_base == "https://custom.api.com/v1"


class TestMiniMaxBotFromConfig:
    """Test MiniMaxBot.from_config class method."""

    def test_from_config(self):
        config = MagicMock()
        config.minimax_api_key = "my-minimax-key"
        bot = MiniMaxBot.from_config(config)
        assert bot.minimax_api_key == "my-minimax-key"
        assert bot.api_base == "https://api.minimax.io/v1"

    def test_from_config_empty_key(self):
        config = MagicMock()
        config.minimax_api_key = ""
        bot = MiniMaxBot.from_config(config)
        assert bot.minimax_api_key == ""


class TestMiniMaxBotClient:
    """Test MiniMaxBot OpenAI client creation."""

    def test_make_openai_client(self):
        bot = MiniMaxBot(minimax_api_key="test-key")
        import httpx

        sess = httpx.AsyncClient()
        client = bot._make_openai_client(sess)
        assert client.api_key == "test-key"
        assert str(client.base_url) == "https://api.minimax.io/v1/"

    def test_make_openai_client_custom_base(self):
        bot = MiniMaxBot(
            minimax_api_key="test-key",
            api_base="https://custom.api.com/v1",
        )
        import httpx

        sess = httpx.AsyncClient()
        client = bot._make_openai_client(sess)
        assert str(client.base_url) == "https://custom.api.com/v1/"


class TestMiniMaxBotHistory:
    """Test MiniMaxBot history management."""

    def test_has_history_empty(self):
        bot = MiniMaxBot(minimax_api_key="test-key")
        assert bot.has_history() is False

    def test_has_history_with_data(self):
        bot = MiniMaxBot(minimax_api_key="test-key")
        bot.history = [("hello", "hi")]
        assert bot.has_history() is True

    def test_get_messages(self):
        bot = MiniMaxBot(minimax_api_key="test-key")
        bot.history = [["hello", "hi"], ["how are you", "fine"]]
        messages = bot.get_messages()
        assert len(messages) == 4
        assert messages[0] == {"role": "user", "content": "hello"}
        assert messages[1] == {"role": "assistant", "content": "hi"}

    def test_change_prompt(self):
        bot = MiniMaxBot(minimax_api_key="test-key")
        bot.history = [["old prompt", "response"]]
        bot.change_prompt("new prompt")
        assert bot.history[0][0] == "new prompt"


class TestMiniMaxBotAsk:
    """Test MiniMaxBot ask methods."""

    @pytest.mark.asyncio
    async def test_ask(self):
        bot = MiniMaxBot(minimax_api_key="test-key")
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content="Hello from MiniMax!"))
        ]

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

        with patch.object(bot, "_make_openai_client", return_value=mock_client):
            result = await bot.ask("Hello")
            assert result == "Hello from MiniMax!"
            assert len(bot.history) == 1

    @pytest.mark.asyncio
    async def test_ask_error_returns_empty(self):
        bot = MiniMaxBot(minimax_api_key="test-key")
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("API Error")
        )

        with patch.object(bot, "_make_openai_client", return_value=mock_client):
            result = await bot.ask("Hello")
            assert result == ""

    @pytest.mark.asyncio
    async def test_ask_stream(self):
        bot = MiniMaxBot(minimax_api_key="test-key")

        chunk1 = MagicMock()
        chunk1.choices = [MagicMock(delta=MagicMock(content="Hello"))]
        chunk2 = MagicMock()
        chunk2.choices = [MagicMock(delta=MagicMock(content=" world"))]
        chunk3 = MagicMock()
        chunk3.choices = [MagicMock(delta=MagicMock(content="。"))]

        async def mock_stream():
            for chunk in [chunk1, chunk2, chunk3]:
                yield chunk

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_stream())

        with patch.object(bot, "_make_openai_client", return_value=mock_client):
            sentences = []
            async for sentence in bot.ask_stream("Hello"):
                sentences.append(sentence)
            assert len(sentences) > 0


class TestMiniMaxBotRegistration:
    """Test MiniMaxBot registration in bot registry."""

    def test_bot_in_registry(self):
        from xiaogpt.bot import BOTS

        assert "minimax" in BOTS
        assert BOTS["minimax"] is MiniMaxBot

    def test_minimax_in_all_export(self):
        import xiaogpt.bot as bot_module

        assert "MiniMaxBot" in bot_module.__all__

    def test_get_bot_minimax(self):
        from xiaogpt.bot import get_bot

        config = MagicMock()
        config.bot = "minimax"
        config.minimax_api_key = "test-key"
        bot = get_bot(config)
        assert isinstance(bot, MiniMaxBot)
        assert bot.minimax_api_key == "test-key"


class TestMiniMaxConfig:
    """Test MiniMax config integration."""

    def test_minimax_api_key_field_exists(self):
        from xiaogpt.config import Config

        assert "minimax_api_key" in Config.__dataclass_fields__

    def test_minimax_api_key_env_var(self):
        import os
        from xiaogpt.config import Config

        # Config reads MINIMAX_API_KEY from env
        field = Config.__dataclass_fields__["minimax_api_key"]
        assert field.default == os.getenv("MINIMAX_API_KEY", "")

    def test_minimax_validation_exists(self):
        with open("xiaogpt/config.py") as f:
            content = f.read()
        assert 'self.bot == "minimax"' in content
        assert "MINIMAX_API_KEY" in content

    def test_minimax_validation_raises(self):
        from xiaogpt.config import Config

        with pytest.raises(Exception, match="MINIMAX_API_KEY"):
            Config(bot="minimax", minimax_api_key="", account="a", password="p")

    def test_use_minimax_config_parsing(self):
        with open("xiaogpt/config.py") as f:
            content = f.read()
        assert '"use_minimax"' in content


class TestMiniMaxCLI:
    """Test MiniMax CLI integration."""

    def test_minimax_api_key_arg(self):
        with open("xiaogpt/cli.py") as f:
            content = f.read()
        assert "--minimax_api_key" in content

    def test_use_minimax_arg(self):
        with open("xiaogpt/cli.py") as f:
            content = f.read()
        assert "--use_minimax" in content

    def test_minimax_in_bot_choices(self):
        with open("xiaogpt/cli.py") as f:
            content = f.read()
        assert '"minimax"' in content
