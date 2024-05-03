import httpx
from groq import Groq as openai
from groq import AsyncGroq as AsyncOpenAI

from xiaogpt.bot.chatgptapi_bot import ChatGPTBot


class LlamaBot(ChatGPTBot):
    name = "llama"
    default_options = {"model": "llama3-70b-8192"}

    def __init__(self, llama_api_key: str) -> None:
        self.llama_api_key = llama_api_key
        self.history: list[tuple[str, str]] = []

    def _make_openai_client(self, sess: httpx.AsyncClient) -> AsyncOpenAI:
        return AsyncOpenAI(
            api_key=self.llama_api_key, http_client=sess, base_url=self.api_base
        )

    @classmethod
    def from_config(cls, config):
        return cls(
            llama_api_key=config.llama_api_key,
        )
