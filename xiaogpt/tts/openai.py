from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import httpx

from xiaogpt.tts.base import AudioFileTTS
from xiaogpt.utils import calculate_tts_elapse

if TYPE_CHECKING:
    import openai


class OpenAITTS(AudioFileTTS):
    default_voice = "alloy"

    async def make_audio_file(self, query: str, text: str) -> tuple[Path, float]:
        output_file = tempfile.NamedTemporaryFile(
            suffix=".mp3", mode="wb", delete=False, dir=self.dirname.name
        )
        httpx_kwargs = {}
        if self.config.proxy:
            httpx_kwargs["proxies"] = self.config.proxy
        async with httpx.AsyncClient(trust_env=True, **httpx_kwargs) as sess:
            client = self._make_openai_client(sess)

            resp = await client.audio.speech.create(
                model="tts-1",
                input=text,
                voice=self.config.tts_voice or self.default_voice,
            )
            resp.stream_to_file(output_file.name)
        return Path(output_file.name), calculate_tts_elapse(text)

    def _make_openai_client(self, sess: httpx.AsyncClient) -> openai.AsyncOpenAI:
        import openai

        api_base = self.config.api_base
        if api_base and api_base.rstrip("/").endswith("openai.azure.com"):
            raise NotImplementedError("TTS is not supported for Azure OpenAI")
        else:
            return openai.AsyncOpenAI(
                api_key=self.config.openai_key, http_client=sess, base_url=api_base
            )
