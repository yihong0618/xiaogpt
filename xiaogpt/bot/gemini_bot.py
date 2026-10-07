"""Google Gemini bot"""

from __future__ import annotations

from typing import Any

from rich import print

from xiaogpt.bot.base_bot import BaseBot, ChatHistoryMixin

generation_config = {
    "temperature": 0.7,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 4096,
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

    def __init__(
        self, gemini_key: str, gemini_api_domain: str, gemini_model: str
    ) -> None:
        from google.genai import types

        self.client_options = {"api_key": gemini_key}
        if gemini_api_domain:
            print("Use custom gemini_api_domain: " + gemini_api_domain)
            base_url = gemini_api_domain.rstrip("/")
            if not base_url.startswith(("http://", "https://")):
                base_url = "https://" + base_url
            self.client_options["http_options"] = types.HttpOptions(base_url=base_url)

        self.history = []
        self.model = gemini_model or "gemini-2.0-flash-lite"
        self.generation_config = types.GenerateContentConfig(
            **generation_config,
            safety_settings=safety_settings,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            ),
        )

    def _get_contents(self, query: str):
        from google.genai import types

        messages = self.get_messages() + [{"role": "user", "content": query}]
        return [
            types.Content(
                role="model" if message["role"] == "assistant" else "user",
                parts=[types.Part.from_text(text=message["content"])],
            )
            for message in messages
        ]

    @classmethod
    def from_config(cls, config):
        return cls(
            gemini_key=config.gemini_key,
            gemini_api_domain=config.gemini_api_domain,
            gemini_model=config.gemini_model,
        )

    async def ask(self, query, **options):
        from google import genai

        async with genai.Client(**self.client_options).aio as client:
            response = await client.models.generate_content(
                model=self.model,
                contents=self._get_contents(query),
                config=self.generation_config,
            )
        message = (response.text or "").strip()
        self.add_message(query, message)
        print(message)
        return message

    async def ask_stream(self, query: str, **options: Any):
        from google import genai

        message = ""
        async with genai.Client(**self.client_options).aio as client:
            response = await client.models.generate_content_stream(
                model=self.model,
                contents=self._get_contents(query),
                config=self.generation_config,
            )
            async for chunk in response:
                if chunk.text:
                    message += chunk.text
                    print(chunk.text, end="")
                    yield chunk.text
        self.add_message(query, message)
