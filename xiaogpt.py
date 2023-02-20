import argparse
import json
import subprocess
import time
from http.cookies import SimpleCookie
from pathlib import Path

import requests
from requests.utils import cookiejar_from_dict
from revChatGPT.V1 import Chatbot, configure
from rich import print

LATEST_ASK_API = "https://userprofile.mina.mi.com/device_profile/v2/conversation?source=dialogu&hardware={hardware}&timestamp={timestamp}&limit=2"
COOKIE_TEMPLATE = "deviceId={device_id}; serviceToken={service_token}; userId={user_id}"

HARDWARE_COMMAND_DICT = {
    "LX06": "5-1",
    "L05B": "5-3",
    # add more here
}


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
    def __init__(self, hardware, conversation_id="", cookie=""):
        self.mi_token_home = Path.home() / ".mi.token"
        self.hardware = hardware
        self.cookie_string = ""
        self.last_timestamp = 0  # timestamp last call mi speaker
        self.s = requests.session()
        self.chatbot = None  # a little slow to init we move it after xiaomi init
        self.user_id = ""
        self.device_id = ""
        self.service_token = ""
        self.cookie = cookie
        self.tts_command = HARDWARE_COMMAND_DICT.get(hardware, "5-1")
        self.conversation_id = conversation_id

    def _init_all_data(self):
        # Step 1 make sure we init the ai api and servive token
        try:
            # micli mina to make sure the init
            mi_hardware_data = json.loads(subprocess.check_output(["micli", "mina"]))
        except Exception as e:
            raise Exception(
                "Something is wrong with get data, please visit https://github.com/Yonsm/MiService"
            )

        # Step 2 get user_id and ai service_token
        with open(self.mi_token_home) as f:
            user_data = json.loads(f.read())
        self.user_id = user_data.get("userId")
        self.service_token = user_data.get("micoapi")[1]
        self._init_data_hardware(mi_hardware_data)
        # Step 3 init get get message api's cookie
        self._init_cookie()
        # Step 4 init first data and chatbot
        self._init_first_data_and_chatbot()

    def _init_data_hardware(self, hardware_data):
        if self.cookie:
            # if use cookie do not need init
            return
        for h in hardware_data:
            if h.get("hardware", "") == self.hardware:
                self.device_id = h.get("deviceID")
                break
        else:
            raise Exception(f"we have no hardware: {self.hardware} please check")

    def _init_cookie(self):
        if self.cookie:
            self.s.cookies = parse_cookie_string(self.cookie)
        else:
            self.cookie_string = COOKIE_TEMPLATE.format(
                device_id=self.device_id,
                service_token=self.service_token,
                user_id=self.user_id,
            )
            self.s.cookies = parse_cookie_string(self.cookie_string)

    def _init_first_data_and_chatbot(self):
        data = self.get_latest_ask_from_xiaoai()
        self.last_timestamp, self.last_record = self.get_last_timestamp_and_record(data)
        self.chatbot = Chatbot(configure())

    def get_latest_ask_from_xiaoai(self):
        r = self.s.get(
            LATEST_ASK_API.format(
                hardware=self.hardware, timestamp=str(int(time.time() * 1000))
            )
        )
        return r.json()

    def get_last_timestamp_and_record(self, data):
        if d := data.get("data"):
            records = json.loads(d).get("records")
            last_record = records[0]
            timestamp = last_record.get("time")
            return timestamp, last_record
        else:
            return 0, None

    def do_action(self, command, value):
        # print(f"MiService: do_action {command}:{value}")
        result = subprocess.check_output(["micli", command, value])

    def normalize(self, message):
        message = message.replace(" ", "，")
        message = message.replace("\n", "，")
        message = message.replace('"', "，")

        return message

    def run_forever(self):
        self._init_all_data()
        while 1:
            print(f"Now listening xiaoai new message timestamp: {self.last_timestamp}")
            try:
                r = self.get_latest_ask_from_xiaoai()
            except Exception:
                # we try to init all again
                self._init_all_data()
                r = self.get_latest_ask_from_xiaoai()

            time.sleep(5)
            new_timestamp, last_record = self.get_last_timestamp_and_record(r)
            if new_timestamp > self.last_timestamp:
                self.last_timestamp = new_timestamp
                query = last_record.get("query", "")
                if query.find("帮我回答") != -1:
                    # drop 帮我回答
                    query = query[4:] + "，请用100字以内回答"
                    print(query)
                    print("Running chatgpt ask maybe a little slow we do not pay")
                    # waiting for xiaoai speaker done
                    time.sleep(8)
                    self.do_action(self.tts_command, "正在问GPT我们不是会员还用的API有点慢")
                    if self.conversation_id:
                        data = list(self.chatbot.ask(query))[-1]
                    else:
                        data = list(
                            self.chatbot.ask(
                                query, conversation_id=self.conversation_id
                            )
                        )[-1]
                    if message := data.get("message", ""):
                        # xiaoai tts did not support space
                        message = self.normalize(message)
                        message = "以下是GPT的回答:" + message
                        print(message)
                        try:
                            print(
                                "以下是小爱的回答: ",
                                last_record.get("answers")[0]
                                .get("tts", {})
                                .get("text"),
                            )
                        except:
                            print("小爱没回")
                        # 5-1 for xiaoai pro tts
                        # TODO more data to chunk
                        try:
                            self.do_action(self.tts_command, message)
                            time.sleep(1)
                        except Exception as e:
                            print("Something is wrong: ", str(e))

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
        "--cookie",
        dest="cookie",
        type=str,
        default="",
        help="xiaomi cookie",
    )
    options = parser.parse_args()
    miboy = MiGPT(options.hardware, options.conversation_id, options.cookie)
    miboy._init_all_data()
    miboy.run_forever()
