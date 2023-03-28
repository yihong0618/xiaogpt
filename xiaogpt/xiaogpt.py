#!/usr/bin/env python3
import asyncio
import functools
import http.server
import json
import logging
import os
import random
import re
import socket
import socketserver
import tempfile
import threading
import time
from pathlib import Path

import edge_tts
import openai
from aiohttp import ClientSession
from miservice import MiAccount, MiIOService, MiNAService, miio_command
from rich import print
from rich.logging import RichHandler

from xiaogpt.bot import ChatGPTBot, GPT3Bot
from xiaogpt.config import (
    COOKIE_TEMPLATE,
    EDGE_TTS_DICT,
    LATEST_ASK_API,
    MI_ASK_SIMULATE_DATA,
    WAKEUP_KEYWORD,
    Config,
)
from xiaogpt.utils import (
    calculate_tts_elapse,
    find_key_by_partial_string,
    parse_cookie_string,
)

EOF = object()


class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


class HTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    logger = logging.getLogger("xiaogpt")

    def log_message(self, format, *args):
        self.logger.debug(f"{self.address_string()} - {format}", *args)

    def log_error(self, format, *args):
        self.logger.error(f"{self.address_string()} - {format}", *args)

    def copyfile(self, source, outputfile):
        try:
            super().copyfile(source, outputfile)
        except (socket.error, ConnectionResetError, BrokenPipeError):
            # ignore this or TODO find out why the error later
            pass


class MiGPT:
    def __init__(self, config: Config):
        self.config = config

        self.mi_token_home = Path.home() / ".mi.token"
        self.last_timestamp = int(time.time() * 1000)  # timestamp last call mi speaker
        self.last_record = None
        self.cookie_jar = None
        self._chatbot = None
        self.device_id = ""
        self.parent_id = None
        self.mina_service = None
        self.miio_service = None
        self.in_conversation = False
        self.polling_event = asyncio.Event()
        self.new_record_event = asyncio.Event()
        self.temp_dir = None

        # setup logger
        self.log = logging.getLogger("xiaogpt")
        self.log.setLevel(logging.DEBUG if config.verbose else logging.INFO)
        self.log.addHandler(RichHandler())
        self.log.debug(config)

    async def poll_latest_ask(self):
        async with ClientSession() as session:
            session._cookie_jar = self.cookie_jar
            while True:
                self.log.debug(
                    "Now listening xiaoai new message timestamp: %s",
                    self.last_timestamp,
                )
                await self.get_latest_ask_from_xiaoai(session)
                start = time.perf_counter()
                await self.polling_event.wait()
                if (d := time.perf_counter() - start) < 1:
                    # sleep to avoid too many request
                    await asyncio.sleep(1 - d)

    async def init_all_data(self, session):
        await self.login_miboy(session)
        await self._init_data_hardware()
        session.cookie_jar.update_cookies(self.get_cookie())
        self.cookie_jar = session.cookie_jar
        if self.config.enable_edge_tts:
            self.start_http_server()

    async def login_miboy(self, session):
        account = MiAccount(
            session,
            self.config.account,
            self.config.password,
            str(self.mi_token_home),
        )
        # Forced login to refresh to refresh token
        await account.login("micoapi")
        self.mina_service = MiNAService(account)
        self.miio_service = MiIOService(account)

    async def _init_data_hardware(self):
        if self.config.cookie:
            # if use cookie do not need init
            return
        hardware_data = await self.mina_service.device_list()
        for h in hardware_data:
            if h.get("hardware", "") == self.config.hardware:
                self.device_id = h.get("deviceID")
                break
        else:
            raise Exception(
                f"we have no hardware: {self.config.hardware} please use `micli mina` to check"
            )
        if not self.config.mi_did:
            devices = await self.miio_service.device_list()
            try:
                self.config.mi_did = next(
                    d["did"]
                    for d in devices
                    if d["model"].endswith(self.config.hardware.lower())
                )
            except StopIteration:
                raise Exception(
                    f"cannot find did for hardware: {self.config.hardware} "
                    "please set it via MI_DID env"
                )

    def get_cookie(self):
        if self.config.cookie:
            cookie_jar = parse_cookie_string(self.config.cookie)
            # set attr from cookie fix #134
            cookie_dict = cookie_jar.get_dict()
            self.device_id = cookie_dict["deviceId"]
            return cookie_jar
        else:
            with open(self.mi_token_home) as f:
                user_data = json.loads(f.read())
            user_id = user_data.get("userId")
            service_token = user_data.get("micoapi")[1]
            cookie_string = COOKIE_TEMPLATE.format(
                device_id=self.device_id, service_token=service_token, user_id=user_id
            )
            return parse_cookie_string(cookie_string)

    @property
    def chatbot(self):
        if self._chatbot is None:
            if self.config.bot == "gpt3":
                self._chatbot = GPT3Bot(self.config.openai_key, self.config.api_base)
            elif self.config.bot == "chatgptapi":
                self._chatbot = ChatGPTBot(self.config.openai_key, self.config.api_base)
            else:
                raise Exception(f"Do not support {self.config.bot}")
        return self._chatbot

    async def simulate_xiaoai_question(self):
        data = MI_ASK_SIMULATE_DATA
        # Convert the data['data'] value from a string to a dictionary
        data_dict = json.loads(data["data"])
        # Get the first item in the records list
        record = data_dict["records"][0]
        # Replace the query and time values with user input
        record["query"] = input("Enter the new query: ")
        record["time"] = int(time.time() * 1000)
        # Convert the updated data_dict back to a string and update the data['data'] value
        data["data"] = json.dumps(data_dict)
        await asyncio.sleep(1)

        return data

    def need_ask_gpt(self, record):
        query = record.get("query", "")
        return (
            self.in_conversation
            and not query.startswith(WAKEUP_KEYWORD)
            or query.startswith(tuple(self.config.keyword))
        )

    def need_change_prompt(self, record):
        if self.config.bot == "gpt3":
            return False
        query = record.get("query", "")
        return (
            self.in_conversation
            and not query.startswith(WAKEUP_KEYWORD)
            or query.startswith(tuple(self.config.change_prompt_keyword))
        )

    def _change_prompt(self, new_prompt):
        new_prompt = re.sub(
            rf"^({'|'.join(self.config.change_prompt_keyword)})", "", new_prompt
        )
        new_prompt = "以下都" + new_prompt
        print(f"Prompt from {self.config.prompt} change to {new_prompt}")
        self.config.prompt = new_prompt
        if self.chatbot.history:
            print(self.chatbot.history)
            self.chatbot.history[0][0] = new_prompt

    async def get_latest_ask_from_xiaoai(self, session):
        retries = 2
        for _ in range(retries):
            r = await session.get(
                LATEST_ASK_API.format(
                    hardware=self.config.hardware,
                    timestamp=str(int(time.time() * 1000)),
                )
            )
            try:
                data = await r.json()
            except Exception:
                self.log.warning("get latest ask from xiaoai error, retry")
            else:
                return self._get_last_query(data)

    def _get_last_query(self, data):
        if d := data.get("data"):
            records = json.loads(d).get("records")
            if not records:
                return
            last_record = records[0]
            timestamp = last_record.get("time")
            if timestamp > self.last_timestamp:
                self.last_timestamp = timestamp
                self.last_record = last_record
                self.new_record_event.set()

    async def do_tts(self, value, wait_for_finish=False):
        if not self.config.use_command:
            try:
                await self.mina_service.text_to_speech(self.device_id, value)
            except Exception:
                pass
        else:
            await miio_command(
                self.miio_service,
                self.config.mi_did,
                f"{self.config.tts_command} {value}",
            )
        if wait_for_finish:
            elapse = calculate_tts_elapse(value)
            await asyncio.sleep(elapse)
            await self.wait_for_tts_finish()

    async def wait_for_tts_finish(self):
        while True:
            if not await self.get_if_xiaoai_is_playing():
                break
            await asyncio.sleep(1)

    def start_http_server(self):
        # set the port range
        port_range = range(8050, 8090)
        # get a random port from the range
        self.port = random.choice(port_range)
        self.temp_dir = tempfile.TemporaryDirectory(prefix="xiaogpt-tts-")
        # create the server
        handler = functools.partial(HTTPRequestHandler, directory=self.temp_dir.name)
        httpd = ThreadedHTTPServer(("", self.port), handler)
        # start the server in a new thread
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        # local ip
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        self.local_ip = s.getsockname()[0]
        s.close()
        self.log.info(f"Serving on {self.local_ip}:{self.port}")

    async def text2mp3(self, text, tts_lang):
        communicate = edge_tts.Communicate(text, tts_lang)
        duration = 0
        with tempfile.NamedTemporaryFile(
            "wb", suffix=".mp3", delete=False, dir=self.temp_dir.name
        ) as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    duration = (chunk["offset"] + chunk["duration"]) / 1e7
            if duration == 0:
                raise RuntimeError(f"Failed to get tts from edge with voice={tts_lang}")
            return (
                f"http://{self.local_ip}:{self.port}/{os.path.basename(f.name)}",
                duration,
            )

    async def edge_tts(self, text_stream, tts_lang):
        async def run_tts(text_stream, tts_lang, queue):
            async for text in text_stream:
                try:
                    url, duration = await self.text2mp3(text, tts_lang)
                except Exception as e:
                    self.log.error(e)
                    continue
                await queue.put((url, duration))

        queue = asyncio.Queue()
        self.log.debug("Edge TTS with voice=%s", tts_lang)
        task = asyncio.create_task(run_tts(text_stream, tts_lang, queue))
        task.add_done_callback(lambda _: queue.put_nowait(EOF))
        while True:
            item = await queue.get()
            if item is EOF:
                break
            url, duration = item
            self.log.debug(f"play: {url}")
            await self.mina_service.play_by_url(self.device_id, url)
            await asyncio.sleep(duration)
            await self.wait_for_tts_finish()
        task.cancel()

    @staticmethod
    def _normalize(message):
        message = message.strip().replace(" ", "--")
        message = message.replace("\n", "，")
        message = message.replace('"', "，")
        return message

    async def ask_gpt(self, query):
        if not self.config.stream:
            async with ClientSession(trust_env=True) as session:
                openai.aiosession.set(session)
                answer = await self.chatbot.ask(query, **self.config.gpt_options)
                message = self._normalize(answer) if answer else ""
                yield message
                return

        async def collect_stream(queue):
            async with ClientSession(trust_env=True) as session:
                openai.aiosession.set(session)
                async for message in self.chatbot.ask_stream(
                    query, **self.config.gpt_options
                ):
                    await queue.put(message)

        self.polling_event.set()
        queue = asyncio.Queue()
        is_eof = False
        task = asyncio.create_task(collect_stream(queue))
        task.add_done_callback(lambda _: queue.put_nowait(EOF))
        while True:
            if is_eof or self.new_record_event.is_set():
                break
            message = await queue.get()
            if message is EOF:
                break
            while not queue.empty():
                if (next_msg := queue.get_nowait()) is EOF:
                    is_eof = True
                    break
                message += next_msg
            if message:
                yield self._normalize(message)
        self.polling_event.clear()
        task.cancel()

    async def get_if_xiaoai_is_playing(self):
        playing_info = await self.mina_service.player_get_status(self.device_id)
        # WTF xiaomi api
        is_playing = (
            json.loads(playing_info.get("data", {}).get("info", "{}")).get("status", -1)
            == 1
        )
        return is_playing

    async def stop_if_xiaoai_is_playing(self):
        is_playing = await self.get_if_xiaoai_is_playing()
        if is_playing:
            # stop it
            await self.mina_service.player_pause(self.device_id)

    async def wakeup_xiaoai(self):
        return await miio_command(
            self.miio_service,
            self.config.mi_did,
            f"{self.config.wakeup_command} {WAKEUP_KEYWORD} 0",
        )

    async def run_forever(self):
        async with ClientSession() as session:
            await self.init_all_data(session)
            task = asyncio.create_task(self.poll_latest_ask())
            assert task is not None  # to keep the reference to task, do not remove this
            print(f"Running xiaogpt now, 用`{'/'.join(self.config.keyword)}`开头来提问")
            print(f"或用`{self.config.start_conversation}`开始持续对话")
            while True:
                self.polling_event.set()
                await self.new_record_event.wait()
                self.new_record_event.clear()
                new_record = self.last_record
                self.polling_event.clear()  # stop polling when processing the question
                query = new_record.get("query", "").strip()

                if query == self.config.start_conversation:
                    if not self.in_conversation:
                        print("开始对话")
                        self.in_conversation = True
                        await self.wakeup_xiaoai()
                    await self.stop_if_xiaoai_is_playing()
                    continue
                elif query == self.config.end_conversation:
                    if self.in_conversation:
                        print("结束对话")
                        self.in_conversation = False
                    await self.stop_if_xiaoai_is_playing()
                    continue

                # we can change prompt
                if self.need_change_prompt(new_record):
                    self._change_prompt(new_record.get("query", ""))

                if not self.need_ask_gpt(new_record):
                    self.log.debug("No new xiao ai record")
                    continue

                # drop 帮我回答
                query = re.sub(rf"^({'|'.join(self.config.keyword)})", "", query)

                print("-" * 20)
                print("问题：" + query + "？")
                if not self.chatbot.history:
                    query = f"{query}，{self.config.prompt}"
                if self.config.mute_xiaoai:
                    await self.stop_if_xiaoai_is_playing()
                else:
                    # waiting for xiaoai speaker done
                    await asyncio.sleep(8)
                await self.do_tts("正在问GPT请耐心等待")
                try:
                    print(
                        "以下是小爱的回答: ",
                        new_record.get("answers", [])[0].get("tts", {}).get("text"),
                    )
                except IndexError:
                    print("小爱没回")
                print("以下是GPT的回答: ", end="")
                try:
                    if not self.config.enable_edge_tts:
                        async for message in self.ask_gpt(query):
                            await self.do_tts(message, wait_for_finish=True)
                    else:
                        tts_lang = (
                            find_key_by_partial_string(EDGE_TTS_DICT, query)
                            or self.config.edge_tts_voice
                        )
                        # tts with edge_tts
                        await self.edge_tts(self.ask_gpt(query), tts_lang)
                    print("回答完毕")
                except Exception as e:
                    print(f"GPT回答出错 {str(e)}")
                if self.in_conversation:
                    print(f"继续对话, 或用`{self.config.end_conversation}`结束对话")
                    await self.wakeup_xiaoai()
