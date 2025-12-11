"""Jiekou AI bot"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, ClassVar

import httpx
from rich import print

from xiaogpt.bot.base_bot import BaseBot, ChatHistoryMixin
from xiaogpt.utils import split_sentences

if TYPE_CHECKING:
    import openai


@dataclasses.dataclass
class JiekouBot(ChatHistoryMixin, BaseBot):
    name: ClassVar[str] = "Jiekou AI"
    default_options: ClassVar[dict[str, str]] = {
        "model": "meta-llama/llama-3.1-8b-instruct"
    }
    jiekou_api_key: str
    api_base: str = "https://api.jiekou.ai/openai"
    proxy: str | None = None
    history: list[tuple[str, str]] = dataclasses.field(default_factory=list, init=False)

    def _make_openai_client(self, sess: httpx.AsyncClient) -> openai.AsyncOpenAI:
        import openai

        return openai.AsyncOpenAI(
            api_key=self.jiekou_api_key,
            base_url=self.api_base,
            http_client=sess,
        )

    @classmethod
    def from_config(cls, config):
        return cls(
            jiekou_api_key=config.jiekou_api_key,
            api_base="https://api.jiekou.ai/openai",
            proxy=config.proxy,
        )

    async def ask(self, query, **options):
        ms = self.get_messages()
        ms.append({"role": "user", "content": f"{query}"})
        kwargs = {**self.default_options, **options}
        httpx_kwargs = {}
        if self.proxy:
            httpx_kwargs["proxies"] = self.proxy
        async with httpx.AsyncClient(trust_env=True, **httpx_kwargs) as sess:
            client = self._make_openai_client(sess)
            try:
                completion = await client.chat.completions.create(messages=ms, **kwargs)
            except Exception as e:
                print(str(e))
                return ""

            message = completion.choices[0].message.content
            self.add_message(query, message)
            print(message)
            return message

    async def ask_stream(self, query, **options):
        ms = self.get_messages()
        ms.append({"role": "user", "content": f"{query}"})
        kwargs = {**self.default_options, **options}
        httpx_kwargs = {}
        if self.proxy:
            httpx_kwargs["proxies"] = self.proxy
        async with httpx.AsyncClient(trust_env=True, **httpx_kwargs) as sess:
            client = self._make_openai_client(sess)
            try:
                completion = await client.chat.completions.create(
                    messages=ms, stream=True, **kwargs
                )
            except Exception as e:
                print(str(e))
                return

            async def text_gen():
                async for event in completion:
                    if not event.choices:
                        continue
                    chunk_message = event.choices[0].delta
                    if chunk_message.content is None:
                        continue
                    print(chunk_message.content, end="")
                    yield chunk_message.content

            message = ""
            try:
                async for sentence in split_sentences(text_gen()):
                    message += sentence
                    yield sentence
            finally:
                print()
                self.add_message(query, message)
