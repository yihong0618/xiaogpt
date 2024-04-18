from typing import AsyncIterator

from miservice import MiIOService, MiNAService, miio_command

from xiaogpt.config import Config
from xiaogpt.tts.base import TTS
from xiaogpt.utils import calculate_tts_elapse


class MiTTS(TTS):
    def __init__(
        self, mina_service: MiNAService, device_id: str, config: Config
    ) -> None:
        super().__init__(mina_service, device_id, config)
        self.miio_service = MiIOService(mina_service.account)

    async def say(self, text: str) -> None:
        if not self.config.use_command:
            try:
                await self.mina_service.text_to_speech(self.device_id, text)
            except Exception:
                pass
        else:
            await miio_command(
                self.miio_service,
                self.config.mi_did,
                f"{self.config.tts_command} {text}",
            )

    async def synthesize(self, lang: str, text_stream: AsyncIterator[str]) -> None:
        async for text in text_stream:
            await self.say(text)
            await self.wait_for_duration(calculate_tts_elapse(text))
