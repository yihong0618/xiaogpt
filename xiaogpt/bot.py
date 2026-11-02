from __future__ import annotations

from typing import Any, AsyncIterator

import httpx2
import republic
from republic.events import TextDelta
from rich import print

import xiaogpt.providers  # noqa: F401  register extra providers
from xiaogpt.config import Config
from xiaogpt.utils import split_sentences

# Keep the latest 5 rounds of conversation
MAX_HISTORY_MESSAGES = 10


class Chatbot:
    """A chat bot backed by Republic, which talks to any supported LLM provider."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.name = config.model.split(":", 1)[1]
        self.history: list[republic.Message] = []
        self._http_client = (
            httpx2.AsyncClient(proxy=config.proxy, timeout=600)
            if config.proxy
            else None
        )
        self.model = republic.get_model(
            config.model,
            api_key=config.api_key or None,
            api_base=config.api_base or None,
            api_format=config.api_format or None,
            http_client=self._http_client,
        )

    def _messages(self, query: str) -> list[republic.Message]:
        messages = list(self.history)
        if self.config.prompt:
            messages.insert(0, republic.system(self.config.prompt))
        messages.append(republic.user(query))
        return messages

    def _add_history(self, query: str, answer: republic.Message) -> None:
        self.history.extend([republic.user(query), answer])
        del self.history[:-MAX_HISTORY_MESSAGES]

    async def ask(self, query: str, **options: Any) -> str:
        response = await self.model.chat(self._messages(query), **options)
        self._add_history(query, response.message)
        print(response.text)
        return response.text

    async def ask_stream(self, query: str, **options: Any) -> AsyncIterator[str]:
        async with self.model.stream(self._messages(query), **options) as stream:

            async def text_gen() -> AsyncIterator[str]:
                async for event in stream:
                    if isinstance(event, TextDelta):
                        print(event.chunk, end="")
                        yield event.chunk

            try:
                async for sentence in split_sentences(text_gen()):
                    yield sentence
            finally:
                print()
        self._add_history(query, stream.response.message)

    async def close(self) -> None:
        await self.model.provider.close()
        if self._http_client is not None:
            await self._http_client.aclose()
