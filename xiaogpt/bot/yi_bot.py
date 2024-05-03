import httpx
import openai

from xiaogpt.bot.chatgptapi_bot import ChatGPTBot


class YiBot(ChatGPTBot):
    name = "yi"
    default_options = {"model": "yi-34b-chat-0205"}

    def __init__(
        self, yi_api_key: str, api_base="https://api.lingyiwanwu.com/v1"
    ) -> None:
        self.yi_api_key = yi_api_key
        self.api_base = api_base
        self.history: list[tuple[str, str]] = []

    def _make_openai_client(self, sess: httpx.AsyncClient) -> openai.AsyncOpenAI:
        return openai.AsyncOpenAI(
            api_key=self.yi_api_key, http_client=sess, base_url=self.api_base
        )

    @classmethod
    def from_config(cls, config):
        return cls(
            yi_api_key=config.yi_api_key,
            api_base="https://api.lingyiwanwu.com/v1",
        )
