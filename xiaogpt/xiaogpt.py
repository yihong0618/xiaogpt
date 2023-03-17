#!/usr/bin/env python3
import asyncio
import json
import re
import time
from pathlib import Path

from aiohttp import ClientSession
from miservice import MiAccount, MiIOService, MiNAService, miio_command
from rich import print

from xiaogpt.bot import ChatGPTBot, GPT3Bot
from xiaogpt.config import (
    COOKIE_TEMPLATE,
    LATEST_ASK_API,
    MI_ASK_SIMULATE_DATA,
    WAKEUP_KEYWORD,
    Config,
)
from xiaogpt.utils import calculate_tts_elapse, parse_cookie_string


class MiGPT:
    def __init__(self, config: Config):
        self.config = config

        self.mi_token_home = Path.home() / ".mi.token"
        self.last_timestamp = int(time.time() * 1000)  # timestamp last call mi speaker
        self.session = None
        self.chatbot = None  # a little slow to init we move it after xiaomi init
        self.device_id = ""
        self.conversation_id = None
        self.parent_id = None
        self.mina_service = None
        self.miio_service = None
        # mute xiaomi in runtime
        self.this_mute_xiaoai = config.mute_xiaoai
        self.in_conversation = False

    async def init_all_data(self, session):
        self.session = session
        await self.login_miboy()
        await self._init_data_hardware()
        self._init_cookie()
        self._init_chatbot()

    async def login_miboy(self):
        account = MiAccount(
            self.session,
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
            raise Exception(f"we have no hardware: {self.config.hardware} please check")
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

    def _init_cookie(self):
        if self.config.cookie:
            cookiejar = parse_cookie_string(self.config.cookie)
        else:
            with open(self.mi_token_home) as f:
                user_data = json.loads(f.read())
            user_id = user_data.get("userId")
            service_token = user_data.get("micoapi")[1]
            cookie_string = COOKIE_TEMPLATE.format(
                device_id=self.device_id, service_token=service_token, user_id=user_id
            )
            cookiejar = parse_cookie_string(cookie_string)
        self.session.cookie_jar.update_cookies(cookiejar)

    def _init_chatbot(self):
        # TODO refactor this
        if self.config.bot == "gpt3":
            self.chatbot = GPT3Bot(self.config.openai_key, self.config.api_base)
        elif self.config.bot == "chatgptapi":
            self.chatbot = ChatGPTBot(self.config.openai_key, self.config.api_base)
        else:
            raise Exception(f"Do not support {self.config.bot}")

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

    async def get_latest_ask_from_xiaoai(self):
        retries = 2
        for _ in range(retries):
            r = await self.session.get(
                LATEST_ASK_API.format(
                    hardware=self.config.hardware,
                    timestamp=str(int(time.time() * 1000)),
                )
            )
            try:
                data = await r.json()
            except Exception:
                if self.config.verbose:
                    print("get latest ask from xiaoai error, retry")
                self.init_all_data(self.session)
            else:
                return self._get_last_query(data)
        return False, None

    def _get_last_query(self, data):
        if d := data.get("data"):
            records = json.loads(d).get("records")
            if not records:
                return False, None
            last_record = records[0]
            timestamp = last_record.get("time")
            if timestamp > self.last_timestamp:
                self.last_timestamp = timestamp
                return self.need_ask_gpt(last_record), last_record
        return False, None

    async def do_tts(self, value, wait_for_finish=False):
        if not self.config.use_command:
            try:
                await self.mina_service.text_to_speech(self.device_id, value)
            except Exception:
                # do nothing is ok
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
            while True:
                if not await self.get_if_xiaoai_is_playing():
                    break
                await asyncio.sleep(2)
            print("回答完毕")

    @staticmethod
    def _normalize(message):
        message = message.strip().replace(" ", "--")
        message = message.replace("\n", "，")
        message = message.replace('"', "，")
        return message

    async def ask_gpt(self, query):
        answer = await self.chatbot.ask(query)
        return self._normalize(answer) if answer else ""

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
        print(f"Running xiaogpt now, 用`{'/'.join(self.config.keyword)}`开头来提问")
        print(f"或用`{self.config.start_conversation}`开始持续对话")
        async with ClientSession() as session:
            await self.init_all_data(session)
            while 1:
                if self.config.verbose:
                    print(
                        f"Now listening xiaoai new message timestamp: {self.last_timestamp}"
                    )
                need_ask_gpt, new_record = await self.get_latest_ask_from_xiaoai()
                # spider rule
                if not self.config.mute_xiaoai:
                    await asyncio.sleep(3)
                else:
                    await asyncio.sleep(0.3)
                    await self.stop_if_xiaoai_is_playing()
                if new_record:
                    if (
                        new_record.get("query", "").strip()
                        == self.config.start_conversation
                    ):
                        if not self.in_conversation:
                            print("开始对话")
                            self.in_conversation = True
                            await self.wakeup_xiaoai()
                        await self.stop_if_xiaoai_is_playing()
                        continue
                    elif (
                        new_record.get("query", "").strip()
                        == self.config.end_conversation
                    ):
                        if self.in_conversation:
                            print("结束对话")
                            self.in_conversation = False
                        await self.stop_if_xiaoai_is_playing()
                        continue
                if not need_ask_gpt:
                    if self.config.verbose:
                        print("No new xiao ai record")
                    continue

                query = new_record.get("query", "")
                # only mute when your clause start's with the keyword
                self.this_mute_xiaoai = False
                # drop 帮我回答
                query = re.sub(rf"^({'|'.join(self.config.keyword)})", "", query)

                print("-" * 20)
                print("问题：" + query + "？")

                query = f"{query}，{self.config.prompt}"
                # waiting for xiaoai speaker done
                if not self.config.mute_xiaoai:
                    await asyncio.sleep(8)
                await self.do_tts("正在问GPT请耐心等待")
                try:
                    print(
                        "以下是小爱的回答: ",
                        new_record.get("answers", [])[0].get("tts", {}).get("text"),
                    )
                except IndexError:
                    print("小爱没回")
                message = await self.ask_gpt(query)
                # tts to xiaoai with ChatGPT answer
                print("以下是GPT的回答: " + message)
                await self.do_tts(message, wait_for_finish=True)
                if self.config.mute_xiaoai:
                    self.this_mute_xiaoai = True
                if self.in_conversation:
                    print(f"继续对话, 或用`{self.config.end_conversation}`结束对话")
                    await self.wakeup_xiaoai()
