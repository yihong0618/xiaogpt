import asyncio
import functools
import os
import random
import socket
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import AsyncIterator

from miservice import MiNAService

from xiaogpt.config import Config
from xiaogpt.tts.base import TTS, logger
from xiaogpt.utils import get_hostname


class HTTPRequestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.debug(f"{self.address_string()} - {format}", *args)

    def log_error(self, format, *args):
        logger.error(f"{self.address_string()} - {format}", *args)

    def copyfile(self, source, outputfile):
        try:
            super().copyfile(source, outputfile)
        except (socket.error, ConnectionResetError, BrokenPipeError):
            # ignore this or TODO find out why the error later
            pass


class TetosFileTTS(TTS):
    """A TTS model that generates audio files locally and plays them via URL."""

    def __init__(
        self, mina_service: MiNAService, device_id: str, config: Config
    ) -> None:
        from tetos import get_speaker

        super().__init__(mina_service, device_id, config)
        self.dirname = tempfile.TemporaryDirectory(prefix="xiaogpt-tts-")
        self._start_http_server()

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

    async def synthesize(self, lang: str, text_stream: AsyncIterator[str]) -> None:
        queue: asyncio.Queue[tuple[str, float]] = asyncio.Queue()
        finished = asyncio.Event()

        async def worker():
            async for text in text_stream:
                path, duration = await self.make_audio_file(lang, text)
                url = f"http://{self.hostname}:{self.port}/{path.name}"
                await queue.put((url, duration))
            finished.set()

        task = asyncio.create_task(worker())

        while True:
            try:
                url, duration = queue.get_nowait()
            except asyncio.QueueEmpty:
                if finished.is_set():
                    break
                else:
                    await asyncio.sleep(0.1)
                    continue
            logger.debug("Playing URL %s (%s seconds)", url, duration)
            await asyncio.gather(
                self.mina_service.play_by_url(self.device_id, url, _type=1),
                self.wait_for_duration(duration),
            )
        await task

    def _start_http_server(self):
        # set the port range
        port_range = range(8050, 8090)
        # get a random port from the range
        self.port = int(os.getenv("XIAOGPT_PORT", random.choice(port_range)))
        # create the server
        handler = functools.partial(HTTPRequestHandler, directory=self.dirname.name)
        httpd = ThreadingHTTPServer(("", self.port), handler)
        # start the server in a new thread
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        self.hostname = get_hostname()
        logger.info(f"Serving on {self.hostname}:{self.port}")
