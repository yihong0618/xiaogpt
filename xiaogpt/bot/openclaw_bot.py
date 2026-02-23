"""OpenClaw bot for xiaogpt — routes queries through OpenClaw sessions API."""

from __future__ import annotations

import dataclasses
import os
from typing import Any, AsyncGenerator, ClassVar

import httpx
from rich import print

from xiaogpt.bot.base_bot import BaseBot, ChatHistoryMixin
from xiaogpt.utils import split_sentences


@dataclasses.dataclass
class OpenClawBot(ChatHistoryMixin, BaseBot):
    """
    Bot that sends queries to an OpenClaw gateway via its OpenAI-compatible API
    or sessions API.

    Two modes:
    1. OpenAI-compatible mode (default): Uses /v1/chat/completions endpoint.
       Set OPENCLAW_API_BASE (e.g. http://localhost:18789/v1).
    2. Sessions mode: Uses OpenClaw sessions_send for richer integration.
       Set OPENCLAW_SESSION_KEY to target a specific session.

    Environment variables:
    - OPENCLAW_API_BASE: Base URL for OpenClaw's OpenAI-compatible API
                         (default: http://localhost:18789/v1)
    - OPENCLAW_API_KEY:  API key if required (default: "openclaw")
    - OPENCLAW_MODEL:    Model to request (default: "default")
    - OPENCLAW_PROMPT:   System prompt (default: "简洁回答，100字以内")
    """

    name: ClassVar[str] = "OpenClaw"

    api_base: str = ""
    api_key: str = "openclaw"
    model: str = "default"
    system_prompt: str = "简洁回答，100字以内"
    history: list[tuple[str, str]] = dataclasses.field(default_factory=list, init=False)

    @classmethod
    def from_config(cls, config) -> OpenClawBot:
        return cls(
            api_base=config.api_base
            or os.getenv("OPENCLAW_API_BASE", "http://localhost:18789/v1"),
            api_key=config.openai_key
            or os.getenv("OPENCLAW_API_KEY", "openclaw"),
            model=os.getenv("OPENCLAW_MODEL", "default"),
            system_prompt=config.prompt or os.getenv("OPENCLAW_PROMPT", "简洁回答，100字以内"),
        )

    def _build_messages(self, query: str) -> list[dict]:
        """Build message list with system prompt, history, and current query."""
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.get_messages())
        messages.append({"role": "user", "content": query})
        return messages

    async def ask(self, query: str, **options: Any) -> str:
        messages = self._build_messages(query)

        async with httpx.AsyncClient(trust_env=True, timeout=60.0) as client:
            try:
                resp = await client.post(
                    f"{self.api_base.rstrip('/')}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": False,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                message = data["choices"][0]["message"]["content"]
                self.add_message(query, message)
                print(f"[OpenClaw] {message}")
                return message
            except Exception as e:
                print(f"[OpenClaw] Error: {e}")
                return f"抱歉，OpenClaw 连接失败: {e}"

    async def ask_stream(self, query: str, **options: Any) -> AsyncGenerator[str, None]:
        messages = self._build_messages(query)

        async with httpx.AsyncClient(trust_env=True, timeout=60.0) as client:
            try:
                resp = await client.post(
                    f"{self.api_base.rstrip('/')}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "stream": True,
                    },
                )
                resp.raise_for_status()
            except Exception as e:
                print(f"[OpenClaw] Stream error: {e}")
                yield f"抱歉，OpenClaw 连接失败: {e}"
                return

            async def text_gen():
                async for line in resp.aiter_lines():
                    line = line.strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        import json

                        data = json.loads(data_str)
                        if not data.get("choices"):
                            continue
                        delta = data["choices"][0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            print(content, end="")
                            yield content
                    except Exception:
                        continue

            message = ""
            try:
                async for sentence in split_sentences(text_gen()):
                    message += sentence
                    yield sentence
            finally:
                print()
                if message:
                    self.add_message(query, message)
