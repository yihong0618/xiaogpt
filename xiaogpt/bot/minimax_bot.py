"""MiniMax bot"""

import httpx
import openai

from xiaogpt.bot.chatgptapi_bot import ChatGPTBot


class MiniMaxBot(ChatGPTBot):
    name = "MiniMax"
    default_options = {"model": "MiniMax-M1"}

    def __init__(
        self, minimax_api_key: str, api_base="https://api.minimax.io/v1"
    ) -> None:
        self.minimax_api_key = minimax_api_key
        self.api_base = api_base
        self.history: list[tuple[str, str]] = []

    def _make_openai_client(self, sess: httpx.AsyncClient) -> openai.AsyncOpenAI:
        return openai.AsyncOpenAI(
            api_key=self.minimax_api_key, http_client=sess, base_url=self.api_base
        )

    @classmethod
    def from_config(cls, config):
        return cls(
            minimax_api_key=config.minimax_api_key,
            api_base="https://api.minimax.io/v1",
        )
