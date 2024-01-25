from __future__ import annotations

import re

from xiaogpt.bot.base_bot import BaseBot, ChatHistoryMixin
from xiaogpt.utils import split_sentences

_reference_link_re = re.compile(r"\[\d+\]: .+?\n+")


class NewBingBot(ChatHistoryMixin, BaseBot):
    name = "Bing"

    def __init__(
        self,
        bing_cookie_path: str = "",
        bing_cookies: dict | None = None,
        proxy: str | None = None,
    ):
        from EdgeGPT import Chatbot

        self.history = []
        self._bot = Chatbot(
            cookiePath=bing_cookie_path, cookies=bing_cookies, proxy=proxy
        )

    @classmethod
    def from_config(cls, config):
        return cls(
            bing_cookie_path=config.bing_cookie_path,
            bing_cookies=config.bing_cookies,
            proxy=config.proxy,
        )

    @staticmethod
    def clean_text(s):
        s = s.replace("**", "")
        s = _reference_link_re.sub("", s)
        s = re.sub(r"\[[\^\d]+\]", "", s)
        return s.strip()

    async def ask(self, query, **options):
        from EdgeGPT import ConversationStyle

        kwargs = {"conversation_style": ConversationStyle.balanced, **options}
        completion = await self._bot.ask(prompt=query, **kwargs)
        try:
            text = self.clean_text(completion["item"]["messages"][1]["text"])
        except Exception as e:
            print(str(e))
            return
        print(text)
        return text

    async def ask_stream(self, query, **options):
        from EdgeGPT import ConversationStyle

        kwargs = {"conversation_style": ConversationStyle.balanced, **options}
        try:
            completion = self._bot.ask_stream(prompt=query, **kwargs)
        except Exception:
            return

        async def text_gen():
            current = ""
            async for final, resp in completion:
                if final:
                    break
                text = self.clean_text(resp)
                if text == current:
                    continue
                diff = text[len(current) :]
                print(diff, end="")
                yield diff
                current = text

        try:
            async for sentence in split_sentences(text_gen()):
                yield sentence
        finally:
            print()
