from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, field
from typing import Any, Iterable, Literal

import yaml

from xiaogpt.utils import validate_proxy

LATEST_ASK_API = "https://userprofile.mina.mi.com/device_profile/v2/conversation?source=dialogu&hardware={hardware}&timestamp={timestamp}&limit=2"
COOKIE_TEMPLATE = "deviceId={device_id}; serviceToken={service_token}; userId={user_id}"
WAKEUP_KEYWORD = "小爱同学"

HARDWARE_COMMAND_DICT = {
    # hardware: (tts_command, wakeup_command)
    "LX06": ("5-1", "5-5"),
    "L05B": ("5-3", "5-4"),
    "S12": ("5-1", "5-5"),  # 第一代小爱，型号 MDZ-25-DA
    "S12A": ("5-1", "5-5"),
    "LX01": ("5-1", "5-5"),
    "L06A": ("5-1", "5-5"),
    "LX04": ("5-1", "5-4"),
    "L05C": ("5-3", "5-4"),
    "L17A": ("7-3", "7-4"),
    "X08E": ("7-3", "7-4"),
    "LX05A": ("5-1", "5-5"),  # 小爱红外版
    "LX5A": ("5-1", "5-5"),  # 小爱红外版
    "L07A": ("5-1", "5-5"),  # Redmi 小爱音箱 Play(l7a)
    "L15A": ("7-3", "7-4"),
    "X6A": ("7-3", "7-4"),  # 小米智能家庭屏 6
    "X10A": ("7-3", "7-4"),  # 小米智能家庭屏 10
    # add more here
}

DEFAULT_COMMAND = ("5-1", "5-5")

KEY_WORD = ("帮我", "请")
CHANGE_PROMPT_KEY_WORD = ("更改提示词",)
PROMPT = "以下请用 300 字以内回答，请只回答文字不要带链接"
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
    # Republic model spec in the form of `provider:model`
    model: str = os.getenv("XIAOGPT_MODEL", "openai:gpt-4o-mini")
    # Defaults to REPUBLIC_<PROVIDER>_API_KEY / REPUBLIC_<PROVIDER>_API_BASE when not given
    api_key: str = ""
    api_base: str | None = None
    # Chat API format, e.g. "chat" for OpenAI-compatible services
    api_format: str | None = None
    volc_access_key: str = os.getenv("VOLC_ACCESS_KEY", "")
    volc_secret_key: str = os.getenv("VOLC_SECRET_KEY", "")
    proxy: str | None = None
    mi_did: str = os.getenv("MI_DID", "")
    keyword: Iterable[str] = KEY_WORD
    change_prompt_keyword: Iterable[str] = CHANGE_PROMPT_KEY_WORD
    prompt: str = PROMPT
    mute_xiaoai: bool = False
    cookie: str = ""
    use_command: bool = False
    verbose: int = 0
    start_conversation: str = "开始持续对话"
    end_conversation: str = "结束持续对话"
    stream: bool = False
    tts: Literal[
        "mi", "edge", "azure", "openai", "baidu", "google", "volc", "minimax", "fish"
    ] = "mi"
    tts_options: dict[str, Any] = field(default_factory=dict)
    gpt_options: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.proxy:
            validate_proxy(self.proxy)
        if "model" in self.gpt_options:
            # Backward compatibility: `gpt_options.model` overrides the model name
            model = self.gpt_options.pop("model")
            if ":" not in model:
                model = f"{self.model.split(':', 1)[0]}:{model}"
            self.model = model
        if ":" not in self.model:
            raise ValueError(
                f"Invalid model {self.model!r}, it must be in the form of `provider:model`, "
                "e.g. openai:gpt-4o-mini"
            )
        if not self.api_key and self.model.startswith("openai:"):
            # Backward compatibility: read the key from OPENAI_API_KEY
            self.api_key = os.getenv("OPENAI_API_KEY", "")

    @property
    def tts_command(self) -> str:
        return HARDWARE_COMMAND_DICT.get(self.hardware, DEFAULT_COMMAND)[0]

    @property
    def wakeup_command(self) -> str:
        return HARDWARE_COMMAND_DICT.get(self.hardware, DEFAULT_COMMAND)[1]

    @classmethod
    def from_options(cls, options: argparse.Namespace) -> Config:
        config = {}
        if options.config:
            config = cls.read_from_file(options.config)
        for key, value in vars(options).items():
            if value is not None and key in cls.__dataclass_fields__:
                config[key] = value
        if config.get("tts") == "volc":
            config.setdefault("tts_options", {}).setdefault(
                "access_key", config.get("volc_access_key")
            )
            config.setdefault("tts_options", {}).setdefault(
                "secret_key", config.get("volc_secret_key")
            )
        elif config.get("tts") == "fish":
            config.setdefault("tts_options", {}).setdefault(
                "api_key", config.get("fish_api_key")
            )
            if voice := config.get("fish_voice_key"):
                config.setdefault("tts_options", {}).setdefault("voice", voice)

        return cls(**config)

    @classmethod
    def read_from_file(cls, config_path: str) -> dict:
        result = {}
        with open(config_path, "rb") as f:
            if config_path.endswith(".json"):
                config = json.load(f)
            else:
                config = yaml.safe_load(f)
            for key, value in config.items():
                if value is None:
                    continue
                if key == "keyword":
                    if not isinstance(value, list):
                        value = [value]
                    value = [kw for kw in value if kw]
                elif key == "openai_key":
                    key = "api_key"
                elif key == "enable_edge_tts":
                    key, value = "tts", "edge"
                if key in cls.__dataclass_fields__:
                    result[key] = value
        return result
