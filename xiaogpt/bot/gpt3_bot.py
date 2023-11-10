from __future__ import annotations
import dataclasses
import openai
import httpx
from rich import print

from xiaogpt.bot.base_bot import BaseBot, ChatHistoryMixin
from xiaogpt.utils import split_sentences


@dataclasses.dataclass
class GPT3Bot(ChatHistoryMixin, BaseBot):
    openai_key: str
    api_base: str | None = None
    proxy: str | None = None
    history: list[tuple[str, str]] = dataclasses.field(default_factory=list, init=False)

    @classmethod
    def from_config(cls, config):
        return cls(
            openai_key=config.openai_key, api_base=config.api_base, proxy=config.proxy
        )

    async def ask(self, query, **options):
        data = {
            "prompt": query,
            "model": "text-davinci-003",
            "max_tokens": 1024,
            "temperature": 1,
            "top_p": 1,
            **options,
        }
        async with httpx.AsyncClient(trust_env=True, proxies=self.proxy) as sess:
            client = openai.AsyncOpenAI(
                api_key=self.openai_key, http_client=sess, base_url=self.api_base
            )
            try:
                completion = await client.completions.create(**data)
            except Exception as e:
                print(str(e))
                return ""
            print(completion.choices[0].text)
            return completion.choices[0].text

    async def ask_stream(self, query, **options):
        data = {
            "prompt": query,
            "model": "text-davinci-003",
            "max_tokens": 1024,
            "temperature": 1,
            "top_p": 1,
            "stream": True,
            **options,
        }
        async with httpx.AsyncClient(trust_env=True, proxies=self.proxy) as sess:
            client = openai.AsyncOpenAI(
                api_key=self.openai_key, http_client=sess, base_url=self.api_base
            )
            try:
                completion = await client.completions.create(**data)
            except Exception as e:
                print(str(e))
                return

            async def text_gen():
                async for event in completion:
                    if not event.choices:
                        continue
                    text = event.choices[0].text
                    print(text, end="")
                    yield text

            try:
                async for sentence in split_sentences(text_gen()):
                    yield sentence
            finally:
                print()
