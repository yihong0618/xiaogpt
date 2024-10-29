from __future__ import annotations

import abc
import asyncio
import json
import logging
from typing import TYPE_CHECKING, AsyncIterator

if TYPE_CHECKING:
    from typing import TypeVar

    from miservice import MiNAService

    from xiaogpt.config import Config

    T = TypeVar("T", bound="TTS")

logger = logging.getLogger(__name__)


class TTS(abc.ABC):
    """An abstract base class for Text-to-Speech models."""

    def __init__(
        self, mina_service: MiNAService, device_id: str, config: Config
    ) -> None:
        self.mina_service = mina_service
        self.device_id = device_id
        self.config = config

    async def wait_for_duration(self, duration: float) -> None:
        """Wait for the specified duration."""
        await asyncio.sleep(duration)
        while True:
            if not await self.get_if_xiaoai_is_playing():
                break
            await asyncio.sleep(1)

    async def get_if_xiaoai_is_playing(self) -> bool:
        playing_info = await self.mina_service.player_get_status(self.device_id)
        # WTF xiaomi api
        is_playing = (
            json.loads(playing_info.get("data", {}).get("info", "{}")).get("status", -1)
            == 1
        )
        return is_playing

    @abc.abstractmethod
    async def synthesize(self, lang: str, text_stream: AsyncIterator[str]) -> None:
        """Synthesize speech from a stream of text."""
        raise NotImplementedError
