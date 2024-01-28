"""ChatGLM bot"""

from __future__ import annotations

from typing import Any

from rich import print

from xiaogpt.bot.base_bot import BaseBot, ChatHistoryMixin


class BardBot(ChatHistoryMixin, BaseBot):
    name = "Bard"

    def __init__(
        self,
        bard_token: str,
    ) -> None:
        from bardapi import BardAsync

        self._bot = BardAsync(token=bard_token)
        self.history = []

    @classmethod
    def from_config(cls, config):
        return cls(bard_token=config.bard_token)

    async def ask(self, query, **options):
        try:
            r = await self._bot.get_answer(query)
        except Exception as e:
            print(str(e))
        print(r["content"])
        return r["content"]

    def ask_stream(self, query: str, **options: Any):
        raise Exception("Bard do not support stream")
