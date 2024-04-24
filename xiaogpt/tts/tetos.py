from __future__ import annotations

import tempfile
from pathlib import Path

from miservice import MiNAService

from xiaogpt.config import Config
from xiaogpt.tts.base import AudioFileTTS


class TetosTTS(AudioFileTTS):
    def __init__(
        self, mina_service: MiNAService, device_id: str, config: Config
    ) -> None:
        from tetos import get_speaker

        super().__init__(mina_service, device_id, config)
        assert config.tts and config.tts != "mi"
        speaker_cls = get_speaker(config.tts)
        try:
            self.speaker = speaker_cls(**config.tts_options)
        except TypeError as e:
            raise ValueError(f"{e}. Please add them via `tts_options` config") from e

    async def make_audio_file(self, lang: str, text: str) -> tuple[Path, float]:
        output_file = tempfile.NamedTemporaryFile(
            suffix=".mp3", mode="wb", delete=False, dir=self.dirname.name
        )
        duration = await self.speaker.synthesize(text, output_file.name, lang=lang)
        return Path(output_file.name), duration
