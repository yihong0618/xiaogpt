import asyncio
import os
import queue
import random
import threading
import uuid
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import AsyncIterator

from miservice import MiNAService

from xiaogpt.config import Config
from xiaogpt.tts.base import TTS, logger
from xiaogpt.utils import get_hostname


@lru_cache(maxsize=64)
def get_queue(key: str) -> queue.Queue[bytes]:
    return queue.Queue()


class HTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "audio/mpeg")
        self.end_headers()
        key = self.path.split("/")[-1]
        queue = get_queue(key)
        while True:
            chunk = queue.get()
            if chunk == b"":
                break
            self.wfile.write(chunk)

    def log_message(self, format, *args):
        logger.debug(f"{self.address_string()} - {format}", *args)

    def log_error(self, format, *args):
        logger.error(f"{self.address_string()} - {format}", *args)


class TetosLiveTTS(TTS):
    """A TTS model that generates audio in real-time."""

    def __init__(
        self, mina_service: MiNAService, device_id: str, config: Config
    ) -> None:
        from tetos import get_speaker

        super().__init__(mina_service, device_id, config)
        self._start_http_server()

        assert config.tts and config.tts != "mi"
        speaker_cls = get_speaker(config.tts)
        try:
            self.speaker = speaker_cls(**config.tts_options)
        except TypeError as e:
            raise ValueError(f"{e}. Please add them via `tts_options` config") from e
        if not hasattr(self.speaker, "live"):
            raise ValueError(f"{config.tts} Speaker does not support live synthesis")

    async def synthesize(self, lang: str, text_stream: AsyncIterator[str]) -> None:
        key = str(uuid.uuid4())
        queue = get_queue(key)

        async def worker():
            async for chunk in self.speaker.live(text_stream, lang):
                queue.put(chunk)
            queue.put(b"")

        task = asyncio.create_task(worker())
        await self.mina_service.play_by_url(
            self.device_id, f"http://{self.hostname}:{self.port}/{key}", _type=1
        )

        while True:
            if await self.get_if_xiaoai_is_playing():
                await asyncio.sleep(1)
            else:
                break
        await task

    def _start_http_server(self):
        # set the port range
        port_range = range(8050, 8090)
        # get a random port from the range
        self.port = int(os.getenv("XIAOGPT_PORT", random.choice(port_range)))
        # create the server
        handler = HTTPRequestHandler
        httpd = ThreadingHTTPServer(("", self.port), handler)
        # start the server in a new thread
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        self.hostname = get_hostname()
        logger.info(f"Serving on {self.hostname}:{self.port}")
