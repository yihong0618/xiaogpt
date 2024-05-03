import httpx
import openai

from xiaogpt.bot.chatgptapi_bot import ChatGPTBot


class MoonshotBot(ChatGPTBot):
    name = "Moonshot"
    default_options = {"model": "moonshot-v1-8k"}

    def __init__(
        self, moonshot_api_key: str, api_base="https://api.moonshot.cn/v1"
    ) -> None:
        self.moonshot_api_key = moonshot_api_key
        self.api_base = api_base
        self.history: list[tuple[str, str]] = []

    def _make_openai_client(self, sess: httpx.AsyncClient) -> openai.AsyncOpenAI:
        return openai.AsyncOpenAI(
            api_key=self.moonshot_api_key, http_client=sess, base_url=self.api_base
        )

    @classmethod
    def from_config(cls, config):
        return cls(
            moonshot_api_key=config.moonshot_api_key,
            api_base="https://api.moonshot.cn/v1",
        )
