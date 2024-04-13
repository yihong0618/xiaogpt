from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Optional

import azure.cognitiveservices.speech as speechsdk

from xiaogpt.tts.base import AudioFileTTS
from xiaogpt.utils import calculate_tts_elapse

logger = logging.getLogger(__name__)


class AzureTTS(AudioFileTTS):
    voice_name = "zh-CN-XiaoxiaoMultilingualNeural"

    async def make_audio_file(self, query: str, text: str) -> tuple[Path, float]:
        output_file = tempfile.NamedTemporaryFile(
            suffix=".mp3", mode="wb", delete=False, dir=self.dirname.name
        )

        speech_synthesizer = self._build_speech_synthesizer(output_file.name)
        result: Optional[speechsdk.SpeechSynthesisResult] = (
            speech_synthesizer.speak_text_async(text).get()
        )
        if result is None:
            raise RuntimeError(
                f"Failed to get tts from azure with voice={self.voice_name}"
            )
        # Check result
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            logger.debug("Speech synthesized for text [{}]".format(text))

            return Path(output_file.name), calculate_tts_elapse(text)
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            logger.warning(f"Speech synthesis canceled: {cancellation_details.reason}")
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                errmsg = f"Error details: {cancellation_details.error_details}"
                logger.error(errmsg)
                raise RuntimeError(errmsg)
        raise RuntimeError(f"Failed to get tts from azure with voice={self.voice_name}")

    def _build_speech_synthesizer(self, filename: str):
        speech_key = self.config.azure_tts_speech_key
        service_region = self.config.azure_tts_service_region
        if not speech_key:
            raise Exception("Azure tts need speech key")
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key, region=service_region
        )
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
        )
        if self.config.proxy:
            host, port, username, password = self._parse_proxy(self.config.proxy)

            if username and password:
                speech_config.set_proxy(
                    hostname=host, port=port, username=username, password=password
                )
            else:
                speech_config.set_proxy(hostname=host, port=port)

        speech_config.speech_synthesis_voice_name = (
            self.config.tts_voice or self.voice_name
        )
        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=speechsdk.audio.AudioOutputConfig(filename=filename),  # type: ignore
        )
        return speech_synthesizer

    def _parse_proxy(self, proxy_str: str):
        proxy_str = proxy_str
        proxy_str_splited = proxy_str.split("://")
        proxy_type = proxy_str_splited[0]
        proxy_addr = proxy_str_splited[1]

        if proxy_type == "http":
            if "@" in proxy_addr:
                proxy_addr_splited = proxy_addr.split("@")
                proxy_auth = proxy_addr_splited[0]
                proxy_addr_netloc = proxy_addr_splited[1]
                proxy_auth_splited = proxy_auth.split(":")
                username = proxy_auth_splited[0]
                password = proxy_auth_splited[1]
            else:
                proxy_addr_netloc = proxy_addr
                username, password = None, None

            proxy_addr_netloc_splited = proxy_addr_netloc.split(":")
            host = proxy_addr_netloc_splited[0]
            port = int(proxy_addr_netloc_splited[1])
            return host, port, username, password
        raise NotImplementedError
