from __future__ import annotations

import tempfile
from pathlib import Path

from miservice import MiNAService
from tetos.base import Speaker

from xiaogpt.config import Config
from xiaogpt.tts.base import AudioFileTTS


class TetosTTS(AudioFileTTS):
    def __init__(
        self, mina_service: MiNAService, device_id: str, config: Config
    ) -> None:
        super().__init__(mina_service, device_id, config)
        self.speaker = self._get_speaker()

    def _get_speaker(self) -> Speaker:
        from tetos.azure import AzureSpeaker
        from tetos.baidu import BaiduSpeaker
        from tetos.edge import EdgeSpeaker
        from tetos.google import GoogleSpeaker
        from tetos.openai import OpenAISpeaker
        from tetos.volc import VolcSpeaker

        options = self.config.tts_options
        allowed_speakers: list[str] = []
        for speaker in (
            OpenAISpeaker,
            EdgeSpeaker,
            AzureSpeaker,
            VolcSpeaker,
            GoogleSpeaker,
            BaiduSpeaker,
        ):
            if (name := speaker.__name__[:-7].lower()) == self.config.tts:
                try:
                    return speaker(**options)
                except TypeError as e:
                    raise ValueError(
                        f"{e}. Please add them via `tts_options` config"
                    ) from e
            else:
                allowed_speakers.append(name)
        raise ValueError(
            f"Unsupported TTS: {self.config.tts}, allowed: {','.join(allowed_speakers)}"
        )

    async def make_audio_file(self, lang: str, text: str) -> tuple[Path, float]:
        output_file = tempfile.NamedTemporaryFile(
            suffix=".mp3", mode="wb", delete=False, dir=self.dirname.name
        )
        duration = await self.speaker.synthesize(text, output_file.name, lang=lang)
        return Path(output_file.name), duration
