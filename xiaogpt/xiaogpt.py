#!/usr/bin/env python3
import asyncio
import json
import re
import subprocess
import time
from pathlib import Path

from aiohttp import ClientSession
from miservice import MiAccount, MiNAService
from revChatGPT.V1 import Chatbot, configure
from rich import print

from xiaogpt.bot import ChatGPTBot, GPT3Bot
from xiaogpt.config import (
    COOKIE_TEMPLATE,
    HARDWARE_COMMAND_DICT,
    KEY_WORD,
    LATEST_ASK_API,
    MI_ASK_SIMULATE_DATA,
    PROMPT,
)
from xiaogpt.utils import calculate_tts_elapse, parse_cookie_string


class MiGPT:
    def __init__(
        self,
        hardware,
        mi_user,
        mi_pass,
        openai_key,
        cookie="",
        use_command=False,
        mute_xiaoai=False,
        use_gpt3=False,
        use_chatgpt_api=False,
        api_base=None,
        verbose=False,
    ):
        # TODO !!!! refactor so many of this shit
        self.mi_token_home = Path.home() / ".mi.token"
        self.hardware = hardware
        self.mi_user = mi_user
        self.mi_pass = mi_pass
        self.openai_key = openai_key
        self.cookie_string = ""
        self.last_timestamp = 0  # timestamp last call mi speaker
        self.session = None
        self.chatbot = None  # a little slow to init we move it after xiaomi init
        self.user_id = ""
        self.device_id = ""
        self.service_token = ""
        self.cookie = cookie
        self.use_command = use_command
        self.tts_command = HARDWARE_COMMAND_DICT.get(hardware, "5-1")
        self.conversation_id = None
        self.parent_id = None
        self.miboy_account = None
        self.mina_service = None
        # try to mute xiaoai config
        self.mute_xiaoai = mute_xiaoai
        # mute xiaomi in runtime
        self.this_mute_xiaoai = mute_xiaoai
        # if use gpt3 api
        self.use_gpt3 = use_gpt3
        self.use_chatgpt_api = use_chatgpt_api
        self.api_base = api_base
        self.verbose = verbose
        # this attr can be re set value in cli
        self.key_word = KEY_WORD
        self.prompt = PROMPT

    async def init_all_data(self, session):
        await self.login_miboy(session)
        await self._init_data_hardware()
        with open(self.mi_token_home) as f:
            user_data = json.loads(f.read())
        self.user_id = user_data.get("userId")
        self.service_token = user_data.get("micoapi")[1]
        self._init_cookie()
        await self._init_first_data_and_chatbot()

    async def login_miboy(self, session):
        self.session = session
        self.account = MiAccount(
            session,
            self.mi_user,
            self.mi_pass,
            str(self.mi_token_home),
        )
        # Forced login to refresh to refresh token
        await self.account.login("micoapi")
        self.mina_service = MiNAService(self.account)

    async def _init_data_hardware(self):
        if self.cookie:
            # if use cookie do not need init
            return
        hardware_data = await self.mina_service.device_list()
        for h in hardware_data:
            if h.get("hardware", "") == self.hardware:
                self.device_id = h.get("deviceID")
                break
        else:
            raise Exception(f"we have no hardware: {self.hardware} please check")

    def _init_cookie(self):
        if self.cookie:
            self.cookie = parse_cookie_string(self.cookie)
        else:
            self.cookie_string = COOKIE_TEMPLATE.format(
                device_id=self.device_id,
                service_token=self.service_token,
                user_id=self.user_id,
            )
            self.cookie = parse_cookie_string(self.cookie_string)

    async def _init_first_data_and_chatbot(self):
        data = await self.get_latest_ask_from_xiaoai()
        self.last_timestamp, self.last_record = self.get_last_timestamp_and_record(data)
        # TODO refactor this
        if self.use_gpt3:
            self.chatbot = GPT3Bot(self.session, self.openai_key)
        elif self.use_chatgpt_api:
            self.chatbot = ChatGPTBot(self.session, self.openai_key, self.api_base)
        else:
            self.chatbot = Chatbot(configure())

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

    async def get_latest_ask_from_xiaoai(self):
        r = await self.session.get(
            LATEST_ASK_API.format(
                hardware=self.hardware, timestamp=str(int(time.time() * 1000))
            ),
            cookies=parse_cookie_string(self.cookie),
        )
        return await r.json()

    def get_last_timestamp_and_record(self, data):
        if d := data.get("data"):
            records = json.loads(d).get("records")
            if not records:
                return 0, None
            last_record = records[0]
            timestamp = last_record.get("time")
            return timestamp, last_record

    async def do_tts(self, value, wait_for_finish=False):
        if not self.use_command:
            try:
                await self.mina_service.text_to_speech(self.device_id, value)
            except:
                # do nothing is ok
                pass
        else:
            subprocess.check_output(["micli", self.tts_command, value])
        if wait_for_finish:
            elapse = calculate_tts_elapse(value)
            await asyncio.sleep(elapse)
            while True:
                if not await self.get_if_xiaoai_is_playing():
                    break
                await asyncio.sleep(2)
            print("回答完毕")

    def _normalize(self, message):
        message = message.strip().replace(" ", "--")
        message = message.replace("\n", "，")
        message = message.replace('"', "，")
        return message

    async def ask_gpt(self, query):
        if self.use_gpt3:
            return await self.ask_gpt3(query)
        elif self.use_chatgpt_api:
            return await self.ask_chatgpt_api(query)
        return await self.ask_chatgpt(query)

    async def ask_chatgpt_api(self, query):
        message = await self.chatbot.ask(query)
        message = self._normalize(message)
        return message

    async def ask_gpt3(self, query):
        data = await self.chatbot.ask(query)
        choices = data.get("choices")
        if not choices:
            print("No reply from gpt3")
        else:
            message = choices[0].get("text", "")
            message = self._normalize(message)
            return message

    async def ask_chatgpt(self, query):
        # TODO maybe use v2 to async it here
        if self.conversation_id and self.parent_id:
            data = list(
                self.chatbot.ask(
                    query,
                    conversation_id=self.conversation_id,
                    parent_id=self.parent_id,
                )
            )[-1]
        else:
            data = list(self.chatbot.ask(query))[-1]
        if message := data.get("message", ""):
            self.conversation_id = data.get("conversation_id")
            self.parent_id = data.get("parent_id")
            # xiaoai tts did not support space
            message = self._normalize(message)
            return message
        return ""

    async def get_if_xiaoai_is_playing(self):
        playing_info = await self.mina_service.player_get_status(self.device_id)
        # WTF xiaomi api
        is_playing = (
            json.loads(playing_info.get("data", {}).get("info", "{}")).get("status", -1)
            == 1
        )
        return is_playing

    async def run_forever(self):
        print(f"Running xiaogpt now, 用`{'/'.join(KEY_WORD)}`开头来提问")
        async with ClientSession() as session:
            await self.init_all_data(session)
            while 1:
                if self.verbose:
                    print(
                        f"Now listening xiaoai new message timestamp: {self.last_timestamp}"
                    )
                try:
                    r = await self.get_latest_ask_from_xiaoai()
                except Exception:
                    # we try to init all again
                    await self.init_all_data(session)
                    r = await self.get_latest_ask_from_xiaoai()
                # spider rule
                if not self.mute_xiaoai:
                    await asyncio.sleep(3)
                else:
                    await asyncio.sleep(0.3)

                new_timestamp, last_record = self.get_last_timestamp_and_record(r)
                if new_timestamp > self.last_timestamp:
                    self.last_timestamp = new_timestamp
                    query = last_record.get("query", "")
                    if query.startswith(tuple(self.key_word)):
                        # only mute when your clause start's with the keyword
                        self.this_mute_xiaoai = False
                        # drop 帮我回答
                        query = re.sub(rf"^({'|'.join(self.key_word)})", "", query)

                        print("-" * 20)
                        print("问题：" + query + "？")

                        query = f"{query}，{PROMPT}"
                        # waiting for xiaoai speaker done
                        if not self.mute_xiaoai:
                            await asyncio.sleep(8)
                        await self.do_tts("正在问GPT请耐心等待")
                        try:
                            print(
                                "以下是小爱的回答: ",
                                last_record.get("answers")[0]
                                .get("tts", {})
                                .get("text"),
                            )
                        except:
                            print("小爱没回")
                        message = await self.ask_gpt(query)
                        # tts to xiaoai with ChatGPT answer
                        print("以下是GPT的回答: " + message)
                        await self.do_tts(message, wait_for_finish=True)
                        if self.mute_xiaoai:
                            self.this_mute_xiaoai = True
                else:
                    if self.verbose:
                        print("No new xiao ai record")
