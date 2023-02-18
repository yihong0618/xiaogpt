import argparse
import json
import subprocess
import time
import os
from http.cookies import SimpleCookie
from pathlib import Path

import requests
from requests.utils import cookiejar_from_dict
from revChatGPT.V1 import Chatbot, configure
from rich import print

LATEST_ASK_API = "https://userprofile.mina.mi.com/device_profile/v2/conversation?source=dialogu&hardware={hardware}&timestamp={timestamp}&limit=2"
COOKIE_TEMPLATE = "deviceId={device_id}; serviceToken={service_token}; userId={user_id}"
USER_NAME = "可爱无敌小朋友"

# Read the CHATGPT_PROMPT, set it in the .bashrc or .zshrc
# export CHATGPT_PROMPT="XXX"
prompt = os.environ.get("CHATGPT_PROMPT")
if prompt:
    CHATGPT_PROMPT = prompt
else:
    # Use a default value if the CHATGPT_PROMPT environment variable is not set
    CHATGPT_PROMPT = "假设你是" + USER_NAME + "的智能语音助手，他是一个5岁的小男孩，他还有其它小名，皮皮，皮皮虾，回答问题的时候活泼一点，可以随便选一个名字，可以适当加上一些语气词，让他喜欢和你说话，让我们继续之前的聊天吧"

print(f"ChatGPT Prompt: {CHATGPT_PROMPT}")

HARDWARE_COMMAND_DICT = {
    "LX06": "5-1",
    "L05B": "5-3",
    "S12A": "5-1",
    "LX01": "5-1"
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
    def __init__(self, hardware, conversation_id):
        self.mi_token_home = Path.home() / ".mi.token"
        self.hardware = hardware
        self.cookie_string = ""
        self.last_timestamp = 0  # timestamp last call mi speaker
        self.s = requests.session()
        self.chatbot = None  # a little slow to init we move it after xiaomi init
        self.user_id = ""
        self.device_id = ""
        self.service_token = ""
        self.tts_command = HARDWARE_COMMAND_DICT.get(hardware, "5-1")
        self.conversation_id = conversation_id

    def _init_all_data(self):
        # Step 1 make sure we init the ai api and servive token
        try:
            # micli mina to make sure the init
            mi_hardware_data = json.loads(subprocess.check_output(["micli", "mina"]))
            # mi_hardware_data = json.loads(result.stdout)
        except Exception as e:
            print(str(e))
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
        # print(hardware_data)
        for h in hardware_data:
            if h.get("hardware", "") == self.hardware:
                self.device_id = h.get("deviceID")
                break
        else:
            raise Exception(f"we have no hardware: {self.hardware} please check")

    def _init_cookie(self):
        self.cookie_string = COOKIE_TEMPLATE.format(
            device_id=self.device_id,
            service_token=self.service_token,
            user_id=self.user_id,
        )
        self.s.cookies = parse_cookie_string(self.cookie_string)

    def _init_first_data_and_chatbot(self):
        data = self.get_latest_ask_from_xiaoai()
        self.last_timestamp, self.last_record = self.get_last_timestamp_and_record(data)
        self.chatbot = Chatbot(configure(), self.conversation_id)

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
        result = subprocess.run(["micli", command, value])
        print(f"MiService: do_action {command}: done, {result}")

    def normalize(self, message):
        message = message.replace(" ", "，")
        message = message.replace("\n", "，")
        message = message.replace("\"", "，")

        return message

    def run_forever(self):
        self.do_action(self.tts_command, f"正在启动小爱同学和{USER_NAME}的智能语音助手的连接,请稍等哦")
        try:
            #setup the ChatGPT with the prompt text
            data = list(self.chatbot.ask(CHATGPT_PROMPT))[-1]
            if message := data.get("message", ""):
                message = self.normalize(message)
                print("ChatGPT:" + message)
                self.do_action(self.tts_command, message)
        except Exception as e:
            print("ChatGPT: setup prompt failure:" + str(e))

        # self._init_all_data()
        while 1:
            # print(f"Waiting for new MiSpeaker message: {self.last_timestamp}")
            try:
                r = self.get_latest_ask_from_xiaoai()
            except Exception:
                # we try to init all again
                self._init_all_data()
                r = self.get_latest_ask_from_xiaoai()

            time.sleep(2)
            new_timestamp, last_record = self.get_last_timestamp_and_record(r)
            if new_timestamp > self.last_timestamp:
                self.last_timestamp = new_timestamp
                query = last_record.get("query", "")
                print(query)
                if query.find("停止") != -1:
                    continue

                if query.find("播放") != -1:
                    continue

                if query.find("打开") != -1:
                    continue

                if query.find("关闭") != -1:
                    continue

                if query.find("天气") != -1:
                    continue

                self.do_action(self.tts_command, f"你的问题是{query},请稍等哦，让我来想一想")
                try:
                    print(f"Ask ChatGPT:{query}")
                    data = list(self.chatbot.ask(query))[-1]
                    if message := data.get("message", ""):
                        # xiaoai tts did not support space
                        message = self.normalize(message)
                        print("ChatGPT:" + message)
                        try:
                            print(
                                "MiSpeaker: ",
                                last_record.get("answers")[0]
                                .get("tts", {})
                                .get("text"),
                            )
                        except:
                            print("No response from MiSpeaker")

                        # Text from ChatGPT to TTS
                        self.do_action(self.tts_command, message)
                        # wait for the TTS finished
                        sleep_time = len(message) / 5
                        print(f"sleep: {sleep_time}s")
                        time.sleep(sleep_time)
                except Exception as e:
                    self.do_action(self.tts_command, "不知道哪里出什么问题了，请重新问问题吧")
                    print("Something is wrong: ", str(e))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--hardware",
        dest="hardware",
        type=str,
        default="S12A",
        help="小爱 hardware",
    )
    parser.add_argument(
        "--conversation_id",
        dest="conversation_id",
        type=str,
        default="c379851d-fbd4-479e-a716-dddc379fbxxx",
        help="ChatGPT conversation_id",
    )
    options = parser.parse_args()
    miboy = MiGPT(options.hardware, options.conversation_id)
    miboy._init_all_data()
    miboy.run_forever()
