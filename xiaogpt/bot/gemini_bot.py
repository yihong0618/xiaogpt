"""Google Gemini bot"""

from __future__ import annotations

from typing import Any

from rich import print

from xiaogpt.bot.base_bot import BaseBot, ChatHistoryMixin

generation_config = {
    "temperature": 0.7,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE",
    },
]


class GeminiBot(ChatHistoryMixin, BaseBot):
    name = "Gemini"

    def __init__(self, gemini_key: str) -> None:
        import google.generativeai as genai

        genai.configure(api_key=gemini_key)
        self.history = []
        model = genai.GenerativeModel(
            model_name="gemini-pro",
            generation_config=generation_config,
            safety_settings=safety_settings,
        )
        self.convo = model.start_chat()

    @classmethod
    def from_config(cls, config):
        return cls(gemini_key=config.gemini_key)

    async def ask(self, query, **options):
        self.convo.send_message(query)
        message = self.convo.last.text.strip()
        print(message)
        if len(self.convo.history) > 10:
            self.convo.history = self.convo.history[2:]
        return message

    async def ask_stream(self, query: str, **options: Any):
        if len(self.convo.history) > 10:
            self.convo.history = self.convo.history[2:]
        response = self.convo.send_message(query, stream=True)
        for chunk in response:
            print(chunk.text)
            yield chunk.text
