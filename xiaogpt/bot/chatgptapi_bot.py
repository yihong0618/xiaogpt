from __future__ import annotations
import dataclasses
from typing import ClassVar
import httpx

import openai
from rich import print

from xiaogpt.bot.base_bot import BaseBot, ChatHistoryMixin
from xiaogpt.utils import split_sentences


@dataclasses.dataclass
class ChatGPTBot(ChatHistoryMixin, BaseBot):
    default_options: ClassVar[dict[str, str]] = {"model": "gpt-3.5-turbo"}
    openai_key: str
    api_base: str | None = None
    proxy: str | None = None
    deployment_id: str | None = None
    history: list[tuple[str, str]] = dataclasses.field(default_factory=list, init=False)

    def _make_openai_client(self, sess: httpx.AsyncClient) -> openai.AsyncOpenAI:
        if self.api_base and self.api_base.rstrip("/").endswith("openai.azure.com"):
            return openai.AsyncAzureOpenAI(
                api_key=self.openai_key,
                azure_endpoint=self.api_base,
                api_version="2023-07-01-preview",
                azure_deployment=self.deployment_id,
                http_client=sess,
            )
        else:
            return openai.AsyncOpenAI(
                api_key=self.openai_key, http_client=sess, base_url=self.api_base
            )

    @classmethod
    def from_config(cls, config):
        return cls(
            openai_key=config.openai_key,
            api_base=config.api_base,
            proxy=config.proxy,
            deployment_id=config.deployment_id,
        )

    async def ask(self, query, **options):
        ms = self.get_messages()
        ms.append({"role": "user", "content": f"{query}"})
        kwargs = {**self.default_options, **options}
        async with httpx.AsyncClient(trust_env=True, proxies=self.proxy) as sess:
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
        async with httpx.AsyncClient(trust_env=True, proxies=self.proxy) as sess:
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
