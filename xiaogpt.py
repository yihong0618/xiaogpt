import argparse
import asyncio
import json
import os
import subprocess
import time
from http.cookies import SimpleCookie
from pathlib import Path

from aiohttp import ClientSession
from miservice import MiAccount, MiNAService
from requests.utils import cookiejar_from_dict
from revChatGPT.V1 import Chatbot, configure
from rich import print

LATEST_ASK_API = "https://userprofile.mina.mi.com/device_profile/v2/conversation?source=dialogu&hardware={hardware}&timestamp={timestamp}&limit=2"
COOKIE_TEMPLATE = "deviceId={device_id}; serviceToken={service_token}; userId={user_id}"

HARDWARE_COMMAND_DICT = {
    "LX06": "5-1",
    "L05B": "5-3",
    "S12A": "5-1",
    "LX01": "5-1"
    # add more here
}
MI_USER = ""
MI_PASS = ""
KEY_WORD = "帮我回答"
PROMPT = "请用100字以内回答"


### HELP FUNCTION ###
def parse_cookie_string(cookie_string):
    cookie = SimpleCookie()
    cookie.load(cookie_string)
    cookies_dict = {}
    cookiejar = None
    for k, m in cookie.items():
        cookies_dict[k] = m.value
        cookiejar = cookiejar_from_dict(cookies_dict, cookiejar=None, overwrite=True)
    return cookiejar


class MiGPT:
    def __init__(
        self,
        hardware,
        conversation_id="",
        cookie="",
        use_command=False,
        mute_xiaoai=False,
    ):
        self.mi_token_home = Path.home() / ".mi.token"
        self.hardware = hardware
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
        self.conversation_id = conversation_id
        self.miboy_account = None
        self.mina_service = None
        # try to mute xiaoai config
        self.mute_xiaoai = mute_xiaoai
        # mute xiaomi in runtime
        self.this_mute_xiaoai = mute_xiaoai

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
        env = os.environ
        self.session = session
        self.account = MiAccount(
            session,
            env.get("MI_USER") or MI_USER,
            env.get("MI_PASS") or MI_PASS,
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
        self.chatbot = Chatbot(configure())

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

    async def do_tts(self, value):
        if not self.use_command:
            try:
                await self.mina_service.text_to_speech(self.device_id, value)
            except:
                # do nothing is ok
                pass
        else:
            subprocess.check_output(["micli", self.tts_command, value])

    def _normalize(self, message):
        message = message.replace(" ", "，")
        message = message.replace("\n", "，")
        message = message.replace('"', "，")
        return message

    async def ask_gpt(self, query):
        # TODO maybe use v2 to async it here
        if self.conversation_id:
            data = list(self.chatbot.ask(query))[-1]
        else:
            data = list(self.chatbot.ask(query, conversation_id=self.conversation_id))[
                -1
            ]
        if message := data.get("message", ""):
            # xiaoai tts did not support space
            message = self._normalize(message)
            message = "以下是GPT的回答:" + message
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

    async def stop_if_xiaoai_is_playing(self):
        is_playing = await self.get_if_xiaoai_is_playing()
        if is_playing:
            # stop it
            await self.mina_service.player_pause(self.device_id)

    async def run_forever(self):
        async with ClientSession() as session:
            await self.init_all_data(session)
            while 1:
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
                if self.this_mute_xiaoai:
                    await self.stop_if_xiaoai_is_playing()
                new_timestamp, last_record = self.get_last_timestamp_and_record(r)
                if new_timestamp > self.last_timestamp:
                    self.last_timestamp = new_timestamp
                    query = last_record.get("query", "")
                    if query.find(KEY_WORD) != -1:
                        self.this_mute_xiaoai = False
                        # drop 帮我回答
                        query = query.replace(KEY_WORD, "")
                        query = f"{query}，{PROMPT}"
                        # waiting for xiaoai speaker done
                        if not self.mute_xiaoai:
                            await asyncio.sleep(8)
                        await self.do_tts("正在问GPT有点慢请耐心等待")
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
                        print(message)
                        await self.do_tts(message)
                        if self.mute_xiaoai:
                            while 1:
                                is_playing = await self.get_if_xiaoai_is_playing()
                                time.sleep(2)
                                if not is_playing:
                                    break
                            self.this_mute_xiaoai = True
                else:
                    print("No new xiao ai record")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--hardware",
        dest="hardware",
        type=str,
        default="LX06",
        help="小爱 hardware",
    )
    parser.add_argument(
        "--conversation_id",
        dest="conversation_id",
        type=str,
        default="",
        help="ChatGPT conversation_id",
    )
    parser.add_argument(
        "--account",
        dest="account",
        type=str,
        default="",
        help="xiaomi account",
    )
    parser.add_argument(
        "--password",
        dest="password",
        type=str,
        default="",
        help="xiaomi password",
    )
    parser.add_argument(
        "--cookie",
        dest="cookie",
        type=str,
        default="",
        help="xiaomi cookie",
    )
    parser.add_argument(
        "--use_command",
        dest="use_command",
        action="store_true",
        help="use command to tts",
    )
    parser.add_argument(
        "--mute_xiaoai",
        dest="mute_xiaoai",
        action="store_true",
        help="try to mute xiaoai answer",
    )
    options = parser.parse_args()
    # if set
    MI_USER = options.account
    MI_PASS = options.password
    miboy = MiGPT(
        options.hardware,
        options.conversation_id,
        options.cookie,
        options.use_command,
        options.mute_xiaoai,
    )
    asyncio.run(miboy.run_forever())
