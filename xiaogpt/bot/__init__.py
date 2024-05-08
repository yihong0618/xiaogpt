from __future__ import annotations

from xiaogpt.bot.base_bot import BaseBot
from xiaogpt.bot.chatgptapi_bot import ChatGPTBot
from xiaogpt.bot.doubao_bot import DoubaoBot
from xiaogpt.bot.gemini_bot import GeminiBot
from xiaogpt.bot.glm_bot import GLMBot
from xiaogpt.bot.langchain_bot import LangChainBot
from xiaogpt.bot.llama_bot import LlamaBot
from xiaogpt.bot.moonshot_bot import MoonshotBot
from xiaogpt.bot.qwen_bot import QwenBot
from xiaogpt.bot.yi_bot import YiBot
from xiaogpt.config import Config

BOTS: dict[str, type[BaseBot]] = {
    "chatgptapi": ChatGPTBot,
    "glm": GLMBot,
    "gemini": GeminiBot,
    "qwen": QwenBot,
    "langchain": LangChainBot,
    "doubao": DoubaoBot,
    "moonshot": MoonshotBot,
    "yi": YiBot,
    "llama": LlamaBot,
}


def get_bot(config: Config) -> BaseBot:
    try:
        return BOTS[config.bot].from_config(config)
    except KeyError:
        raise ValueError(f"Unsupported bot {config.bot}, must be one of {list(BOTS)}")


__all__ = [
    "ChatGPTBot",
    "GLMBot",
    "GeminiBot",
    "MoonshotBot",
    "QwenBot",
    "get_bot",
    "LangChainBot",
    "DoubaoBot",
    "YiBot",
    "LlamaBot",
]
