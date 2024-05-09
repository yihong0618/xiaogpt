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
    "S12": ("5-1", "5-5"),  # 第一代小爱，型号MDZ-25-DA
    "S12A": ("5-1", "5-5"),
    "LX01": ("5-1", "5-5"),
    "L06A": ("5-1", "5-5"),
    "LX04": ("5-1", "5-4"),
    "L05C": ("5-3", "5-4"),
    "L17A": ("7-3", "7-4"),
    "X08E": ("7-3", "7-4"),
    "LX05A": ("5-1", "5-5"),  # 小爱红外版
    "LX5A": ("5-1", "5-5"),  # 小爱红外版
    "L07A": ("5-1", "5-5"),  # Redmi小爱音箱Play(l7a)
    "L15A": ("7-3", "7-4"),
    "X6A": ("7-3", "7-4"),  # 小米智能家庭屏6
    "X10A": ("7-3", "7-4"),  # 小米智能家庭屏10
    # add more here
}

DEFAULT_COMMAND = ("5-1", "5-5")

KEY_WORD = ("帮我", "请")
CHANGE_PROMPT_KEY_WORD = ("更改提示词",)
PROMPT = "以下请用300字以内回答，请只回答文字不要带链接"
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
    moonshot_api_key: str = os.getenv("MOONSHOT_API_KEY", "")
    yi_api_key: str = os.getenv("YI_API_KEY", "")
    llama_api_key: str = os.getenv("GROQ_API_KEY", "")  # use groq
    glm_key: str = os.getenv("CHATGLM_KEY", "")
    gemini_key: str = os.getenv("GEMINI_KEY", "")  # keep the old rule
    qwen_key: str = os.getenv("DASHSCOPE_API_KEY", "")  # keep the old rule
    serpapi_api_key: str = os.getenv("SERPAPI_API_KEY", "")
    gemini_api_domain: str = os.getenv(
        "GEMINI_API_DOMAIN", ""
    )  # 自行部署的 Google Gemini 代理
    volc_access_key: str = os.getenv("VOLC_ACCESS_KEY", "")
    volc_secret_key: str = os.getenv("VOLC_SECRET_KEY", "")
    proxy: str | None = None
    mi_did: str = os.getenv("MI_DID", "")
    keyword: Iterable[str] = KEY_WORD
    change_prompt_keyword: Iterable[str] = CHANGE_PROMPT_KEY_WORD
    prompt: str = PROMPT
    mute_xiaoai: bool = False
    bot: str = "chatgptapi"
    cookie: str = ""
    api_base: str | None = None
    deployment_id: str | None = None
    use_command: bool = False
    verbose: bool = False
    start_conversation: str = "开始持续对话"
    end_conversation: str = "结束持续对话"
    stream: bool = False
    tts: Literal[
        "mi", "edge", "azure", "openai", "baidu", "google", "volc", "minimax"
    ] = "mi"
    tts_options: dict[str, Any] = field(default_factory=dict)
    gpt_options: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.proxy:
            validate_proxy(self.proxy)
        if (
            self.api_base
            and self.api_base.endswith(("openai.azure.com", "openai.azure.com/"))
            and not self.deployment_id
        ):
            raise Exception(
                "Using Azure OpenAI needs deployment_id, read this: "
                "https://learn.microsoft.com/en-us/azure/cognitive-services/openai/how-to/chatgpt?pivots=programming-language-chat-completions"
            )
        if self.bot in ["chatgptapi"]:
            if not self.openai_key:
                raise Exception(
                    "Using GPT api needs openai API key, please google how to"
                )

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
                elif key == "use_chatgpt_api":
                    key, value = "bot", "chatgptapi"
                elif key == "use_newbing":
                    key, value = "bot", "newbing"
                elif key == "use_glm":
                    key, value = "bot", "glm"
                elif key == "use_gemini":
                    key, value = "bot", "gemini"
                elif key == "use_qwen":
                    key, value = "bot", "qwen"
                elif key == "use_doubao":
                    key, value = "bot", "doubao"
                elif key == "use_moonshot":
                    key, value = "bot", "moonshot"
                elif key == "use_yi":
                    key, value = "bot", "yi"
                elif key == "use_llama":
                    key, value = "bot", "llama"
                elif key == "use_langchain":
                    key, value = "bot", "langchain"
                elif key == "enable_edge_tts":
                    key, value = "tts", "edge"
                if key in cls.__dataclass_fields__:
                    result[key] = value
        return result
