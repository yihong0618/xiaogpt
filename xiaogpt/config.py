from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from typing import Iterable

LATEST_ASK_API = "https://userprofile.mina.mi.com/device_profile/v2/conversation?source=dialogu&hardware={hardware}&timestamp={timestamp}&limit=2"
COOKIE_TEMPLATE = "deviceId={device_id}; serviceToken={service_token}; userId={user_id}"
WAKEUP_KEYWORD = "小爱同学"

HARDWARE_COMMAND_DICT = {
    # hardware: (tts_command, wakeup_command)
    "LX06": ("5-1", "5-5"),
    "L05B": ("5-3", "5-4"),
    "S12A": ("5-1", "5-5"),
    "LX01": ("5-1", "5-5"),
    "L06A": ("5-1", "5-5"),
    "LX04": ("5-1", "5-4"),
    "L05C": ("5-3", "5-4"),
    "L17A": ("7-3", "5-4"),
    "X08E": ("7-3", "5-4"),
    "LX05A": ("5-1", "5-5"),  # 小爱红外版
    "LX5A": ("5-1", "5-5"),  # 小爱红外版
    # add more here
}
DEFAULT_COMMAND = ("5-1", "5-5")

KEY_WORD = ("帮我", "请回答")
PROMPT = "请用100字以内回答"
# simulate_xiaoai_question
MI_ASK_SIMULATE_DATA = {
    "code": 0,
    "message": "Success",
    "data": '{"bitSet":[0,1,1],"records":[{"bitSet":[0,1,1,1,1],"answers":[{"bitSet":[0,1,1,1],"type":"TTS","tts":{"bitSet":[0,1],"text":"Fake Answer"}}],"time":1677851434593,"query":"Fake Question","requestId":"fada34f8fa0c3f408ee6761ec7391d85"}],"nextEndTime":1677849207387}',
}


@dataclass
class Config:
    hardware: str = "LX06"
    account: str = os.getenv("MI_USER", "")
    password: str = os.getenv("MI_PASS", "")
    openai_key: str = os.getenv("OPENAI_API_KEY", "")
    mi_did: str = os.getenv("MI_DID", "")
    keyword: Iterable[str] = KEY_WORD
    prompt: str = PROMPT
    mute_xiaoai: bool = False
    bot: str = "chatgpt"
    cookie: str = ""
    api_base: str | None = None
    use_command: bool = False
    verbose: bool = False
    start_conversation: str = "开始持续对话"
    end_conversation: str = "结束持续对话"

    @property
    def tts_command(self) -> str:
        return HARDWARE_COMMAND_DICT.get(self.hardware, DEFAULT_COMMAND)[0]

    @property
    def wakeup_command(self) -> str:
        return HARDWARE_COMMAND_DICT.get(self.hardware, DEFAULT_COMMAND)[1]

    @classmethod
    def from_options(cls, options: argparse.Namespace) -> Config:
        config = cls()
        if options.config:
            config.read_from_config(options.config)
        for key, value in vars(options).items():
            if value is not None and key in config.__dataclass_fields__:
                setattr(config, key, value)
        if not config.openai_key:
            raise Exception("Use gpt-3 api need openai API key, please google how to")
        return config

    def read_from_config(self, config_path: str) -> None:
        with open(config_path, "rb") as f:
            config = json.load(f)
            for key, value in config.items():
                if value is not None and key in self.__dataclass_fields__:
                    if key == "keyword":
                        if not isinstance(value, list):
                            value = [value]
                        value = [kw for kw in value if kw]
                    elif key == "use_chatgpt_api":
                        key, value = "bot", "chatgptapi"
                    elif key == "use_gpt3":
                        key, value = "bot", "gpt3"
                    setattr(self, key, value)
