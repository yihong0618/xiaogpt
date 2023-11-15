import tempfile
from pathlib import Path

import edge_tts

from xiaogpt.config import EDGE_TTS_DICT
from xiaogpt.tts.base import AudioFileTTS
from xiaogpt.utils import find_key_by_partial_string


class EdgeTTS(AudioFileTTS):
    async def make_audio_file(self, query: str, text: str) -> tuple[Path, float]:
        voice = (
            find_key_by_partial_string(EDGE_TTS_DICT, query)
            or self.config.edge_tts_voice
        )
        communicate = edge_tts.Communicate(text, voice, proxy=self.config.proxy)
        duration = 0
        with tempfile.NamedTemporaryFile(
            suffix=".mp3", mode="wb", delete=False, dir=self.dirname.name
        ) as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    duration = (chunk["offset"] + chunk["duration"]) / 1e7
            if duration == 0:
                raise RuntimeError(f"Failed to get tts from edge with voice={voice}")
        return (Path(f.name), duration)
