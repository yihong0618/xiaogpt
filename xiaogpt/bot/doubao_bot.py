"""ChatGLM bot"""

from __future__ import annotations

import json
from typing import Any, AsyncIterator

import httpx
from rich import print

from xiaogpt.bot.base_bot import BaseBot, ChatHistoryMixin
from xiaogpt.config import Config
from xiaogpt.utils import split_sentences


class DoubaoBot(ChatHistoryMixin, BaseBot):
    API_URL = "https://maas-api.ml-platform-cn-beijing.volces.com"
    name = "豆包"
    default_options = {"model": "skylark-chat"}

    def __init__(self, access_key: str, secret_key: str) -> None:
        from tetos.volc import VolcSignAuth

        self.auth = VolcSignAuth(access_key, secret_key, "ml_maas", "cn-beijing")
        self.history = []

    @classmethod
    def from_config(cls, config: Config):
        return cls(access_key=config.volc_access_key, secret_key=config.volc_secret_key)

    def _get_data(self, query: str, **options: Any):
        options = {**self.default_options, **options}
        model = options.pop("model")
        ms = self.get_messages()
        ms.append({"role": "user", "content": query})
        return {"model": {"name": model}, "parameters": options, "messages": ms}

    async def ask(self, query, **options):
        data = self._get_data(query, **options)
        async with httpx.AsyncClient(base_url=self.API_URL, auth=self.auth) as client:
            resp = await client.post("/api/v1/chat", json=data)
            resp.raise_for_status()
            try:
                message = resp.json()["choice"]["message"]["content"]
            except Exception as e:
                print(str(e))
                return
            self.add_message(query, message)
            print(message)
            return message

    async def ask_stream(self, query: str, **options: Any):
        data = self._get_data(query, **options)
        data["stream"] = True

        async def sse_gen(line_iter: AsyncIterator[str]) -> AsyncIterator[str]:
            message = ""
            async for chunk in line_iter:
                if not chunk.startswith("data:"):
                    continue
                message = chunk[5:].strip()
                if message == "[DONE]":
                    break
                data = json.loads(message)
                text = data["choice"]["message"]["content"]
                print(text, end="", flush=True)
                message += text
                yield text
            print()
            self.add_message(query, message)

        async with httpx.AsyncClient(base_url=self.API_URL, auth=self.auth) as client:
            async with client.stream("POST", "/api/v1/chat", json=data) as resp:
                resp.raise_for_status()
                async for sentence in split_sentences(sse_gen(resp.aiter_lines())):
                    yield sentence
