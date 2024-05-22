#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import functools
import json
import logging
import re
import time
from pathlib import Path
from typing import AsyncIterator

from aiohttp import ClientSession, ClientTimeout
from miservice import MiAccount, MiIOService, MiNAService, miio_command
from rich import print
from rich.logging import RichHandler

from xiaogpt.bot import get_bot
from xiaogpt.config import (
    COOKIE_TEMPLATE,
    LATEST_ASK_API,
    MI_ASK_SIMULATE_DATA,
    WAKEUP_KEYWORD,
    Config,
)
from xiaogpt.tts import TTS, MiTTS, TetosTTS
from xiaogpt.utils import detect_language, parse_cookie_string

EOF = object()


class MiGPT:
    def __init__(self, config: Config):
        self.config = config

        self.mi_token_home = Path.home() / ".mi.token"
        self.last_timestamp = int(time.time() * 1000)  # timestamp last call mi speaker
        self.cookie_jar = None
        self.device_id = ""
        self.parent_id = None
        self.mina_service = None
        self.miio_service = None
        self.in_conversation = False
        self.polling_event = asyncio.Event()
        self.last_record = asyncio.Queue(1)
        # setup logger
        self.log = logging.getLogger("xiaogpt")
        self.log.setLevel(logging.DEBUG if config.verbose else logging.INFO)
        self.log.addHandler(RichHandler())
        self.log.debug(config)
        self.mi_session = ClientSession()

    async def close(self):
        await self.mi_session.close()

    async def poll_latest_ask(self):
        async with ClientSession() as session:
            session._cookie_jar = self.cookie_jar
            while True:
                self.log.debug(
                    "Listening new message, timestamp: %s", self.last_timestamp
                )
                new_record = await self.get_latest_ask_from_xiaoai(session)
                start = time.perf_counter()
                self.log.debug(
                    "Polling_event, timestamp: %s %s", self.last_timestamp, new_record
                )
                await self.polling_event.wait()
                if (
                    self.config.mute_xiaoai
                    and new_record
                    and self.need_ask_gpt(new_record)
                ):
                    await self.stop_if_xiaoai_is_playing()
                if (d := time.perf_counter() - start) < 1:
                    # sleep to avoid too many request
                    self.log.debug("Sleep %f, timestamp: %s", d, self.last_timestamp)
                    # if you want force mute xiaoai, comment this line below.
                    await asyncio.sleep(1 - d)

    async def init_all_data(self):
        await self.login_miboy()
        await self._init_data_hardware()
        self.mi_session.cookie_jar.update_cookies(self.get_cookie())
        self.cookie_jar = self.mi_session.cookie_jar
        self.tts  # init tts

    async def login_miboy(self):
        account = MiAccount(
            self.mi_session,
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
        # fix multi xiaoai problems we check did first
        # why we use this way to fix?
        # some videos and articles already in the Internet
        # we do not want to change old way, so we check if miotDID in `env` first
        # to set device id

        for h in hardware_data:
            if did := self.config.mi_did:
                if h.get("miotDID", "") == str(did):
                    self.device_id = h.get("deviceID")
                    break
                else:
                    continue
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

    @functools.cached_property
    def chatbot(self):
        return get_bot(self.config)

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
        if not record:
            return False
        query = record.get("query", "")
        return (
            self.in_conversation
            and not query.startswith(WAKEUP_KEYWORD)
            or query.lower().startswith(tuple(w.lower() for w in self.config.keyword))
        )

    def need_change_prompt(self, record):
        query = record.get("query", "")
        return query.startswith(tuple(self.config.change_prompt_keyword))

    def _change_prompt(self, new_prompt):
        new_prompt = re.sub(
            rf"^({'|'.join(self.config.change_prompt_keyword)})", "", new_prompt
        )
        new_prompt = "以下都" + new_prompt
        print(f"Prompt from {self.config.prompt} change to {new_prompt}")
        self.config.prompt = new_prompt
        self.chatbot.change_prompt(new_prompt)

    async def get_latest_ask_from_xiaoai(self, session: ClientSession) -> dict | None:
        retries = 3
        for i in range(retries):
            try:
                timeout = ClientTimeout(total=15)
                r = await session.get(
                    LATEST_ASK_API.format(
                        hardware=self.config.hardware,
                        timestamp=str(int(time.time() * 1000)),
                    ),
                    timeout=timeout,
                )
            except Exception as e:
                self.log.warning(
                    "Execption when get latest ask from xiaoai: %s", str(e)
                )
                continue
            try:
                data = await r.json()
            except Exception:
                self.log.warning("get latest ask from xiaoai error, retry")
                if i == 1:
                    # tricky way to fix #282 #272 # if it is the third time we re init all data
                    print("Maybe outof date trying to re init it")
                    await self._retry()
            else:
                return self._get_last_query(data)
        return None

    async def _retry(self):
        await self.init_all_data()

    def _get_last_query(self, data: dict) -> dict | None:
        if d := data.get("data"):
            records = json.loads(d).get("records")
            if not records:
                return None
            last_record = records[0]
            timestamp = last_record.get("time")
            if timestamp > self.last_timestamp:
                try:
                    self.last_record.put_nowait(last_record)
                    self.last_timestamp = timestamp
                    return last_record
                except asyncio.QueueFull:
                    pass
        return None

    async def do_tts(self, value):
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

    @functools.cached_property
    def tts(self) -> TTS:
        if self.config.tts == "mi":
            return MiTTS(self.mina_service, self.device_id, self.config)
        else:
            return TetosTTS(self.mina_service, self.device_id, self.config)

    async def wait_for_tts_finish(self):
        while True:
            if not await self.get_if_xiaoai_is_playing():
                break
            await asyncio.sleep(1)

    @staticmethod
    def _normalize(message: str) -> str:
        message = message.strip().replace(" ", "--")
        message = message.replace("\n", "，")
        message = message.replace('"', "，")
        return message

    async def ask_gpt(self, query: str) -> AsyncIterator[str]:
        if not self.config.stream:
            if self.config.bot == "glm":
                answer = self.chatbot.ask(query, **self.config.gpt_options)
            else:
                answer = await self.chatbot.ask(query, **self.config.gpt_options)
            message = self._normalize(answer) if answer else ""
            yield message
            return

        async def collect_stream(queue):
            async for message in self.chatbot.ask_stream(
                query, **self.config.gpt_options
            ):
                await queue.put(message)

        def done_callback(future):
            queue.put_nowait(EOF)
            if future.exception():
                self.log.error(future.exception())

        self.polling_event.set()
        queue = asyncio.Queue()
        is_eof = False
        task = asyncio.create_task(collect_stream(queue))
        task.add_done_callback(done_callback)
        while True:
            if is_eof or not self.last_record.empty():
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
        await self.init_all_data()
        task = asyncio.create_task(self.poll_latest_ask())
        assert task is not None  # to keep the reference to task, do not remove this
        print(
            f"Running xiaogpt now, 用[green]{'/'.join(self.config.keyword)}[/]开头来提问"
        )
        print(f"或用[green]{self.config.start_conversation}[/]开始持续对话")
        while True:
            self.polling_event.set()
            new_record = await self.last_record.get()
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
                print(new_record)
                self._change_prompt(new_record.get("query", ""))

            if not self.need_ask_gpt(new_record):
                self.log.debug("No new xiao ai record")
                continue

            # drop key words
            query = re.sub(rf"^({'|'.join(self.config.keyword)})", "", query)
            # llama3 is not good at Chinese, so we need to add prompt in it.
            if self.config.bot == "llama":
                query = f"你是一个基于llama3 的智能助手，请你跟我对话时，一定使用中文，不要夹杂一些英文单词，甚至英语短语也不能随意使用，但类似于 llama3 这样的专属名词除外, 问题是：{query}"

            print("-" * 20)
            print("问题：" + query + "？")
            if not self.chatbot.has_history():
                query = f"{query}，{self.config.prompt}"
            # some model can not detect the language code, so we need to add it

            if self.config.mute_xiaoai:
                await self.stop_if_xiaoai_is_playing()
            else:
                # waiting for xiaoai speaker done
                await asyncio.sleep(8)
            await self.do_tts(f"正在问{self.chatbot.name}请耐心等待")
            try:
                print(
                    "以下是小爱的回答: ",
                    new_record.get("answers", [])[0].get("tts", {}).get("text"),
                )
            except IndexError:
                print("小爱没回")
            print(f"以下是 {self.chatbot.name} 的回答: ", end="")
            try:
                await self.speak(self.ask_gpt(query))
            except Exception as e:
                print(f"{self.chatbot.name} 回答出错 {str(e)}")
            else:
                print("回答完毕")
            if self.in_conversation:
                print(f"继续对话, 或用`{self.config.end_conversation}`结束对话")
                await self.wakeup_xiaoai()

    async def speak(self, text_stream: AsyncIterator[str]) -> None:
        first_chunk = await text_stream.__anext__()
        # Detect the language from the first chunk
        # Add suffix '-' because tetos expects it to exist when selecting voices
        # however, the nation code is never used.
        lang = detect_language(first_chunk) + "-"

        async def gen():  # reconstruct the generator
            yield first_chunk
            async for text in text_stream:
                yield text

        await self.tts.synthesize(lang, gen())
