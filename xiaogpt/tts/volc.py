from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Optional
import json
import os
import time
import base64
import threading
import httpx

from volcengine.ApiInfo import ApiInfo
from volcengine.Credentials import Credentials
from volcengine.ServiceInfo import ServiceInfo
from volcengine.base.Service import Service


from xiaogpt.tts.base import AudioFileTTS
from xiaogpt.utils import calculate_tts_elapse

logger = logging.getLogger(__name__)


class VolcTTS(AudioFileTTS):
    def __init__(self, mina_service, device_id, config):
        super().__init__(mina_service, device_id, config)
        self.token = get_token(config)
        self.client = httpx.Client()
        logger.info("Initializing VolcTTS {self.token}")

    async def make_audio_file(self, query: str, text: str) -> tuple[Path, float]:
        tts_payload = json.dumps(
            {
                "text": text,
                "speaker": self.config.volc_tts_speaker,
                "audio_config": {
                    "format": "mp3",
                    "sample_rate": 24000,
                    "speech_rate": 0,
                },
            }
        )

        req = {
            "appkey": self.config.volc_tts_app,
            "token": self.token,
            "namespace": "TTS",
            "payload": tts_payload,
        }

        resp = self.client.post("https://sami.bytedance.com/api/v1/invoke", json=req)
        try:
            sami_resp = resp.json()
            logger.info(f"volc sami_resp {resp.status_code}")
            if resp.status_code != 200:
                print(sami_resp)
        except:
            logger.error(f"Failed to get tts from volcengine with voice=zh {text}")

        if sami_resp["status_code"] == 20000000 and len(sami_resp["data"]) > 0:
            audio_data = base64.b64decode(sami_resp["data"])
            with tempfile.NamedTemporaryFile(
                suffix=".mp3", mode="wb", delete=False, dir=self.dirname.name
            ) as f:
                f.write(audio_data)

        return Path(f.name), calculate_tts_elapse(text)


## fetch token and save it to file
## it's aimed to reduce the request to volcengine
## it'll throw error if token is requested too frequently (more than 1 times per minute)
def get_token(config):
    token_file = Path.home() / ".volc.token"
    if not Path.exists(token_file):
        token = request_token_data(config)
    else:
        with open(token_file, "r") as f:
            token = json.load(f)
            if token["expires_at"] < time.time():
                token = request_token_data(config)

    if not Path.exists(token_file):
        with open(token_file, "w") as f:
            json.dump(token, f)
    return token["token"]


def request_token_data(config):
    sami_service = SAMIService()
    sami_service.set_ak(config.volc_accesskey)
    sami_service.set_sk(config.volc_secretkey)

    req = {
        "appkey": config.volc_tts_app,
        "token_version": "volc-auth-v1",
        "expiration": 24 * 3600,
    }
    token = sami_service.common_json_handler("GetToken", req)
    logger.info(f"Got token from volcengine {token}")
    return token


class SAMIService(Service):
    def __init__(self):
        self.service_info = ServiceInfo(
            "open.volcengineapi.com",
            {},
            Credentials("", "", "sami", "cn-north-1"),
            10,
            10,
        )
        self.api_info = {
            "GetToken": ApiInfo(
                "POST", "/", {"Action": "GetToken", "Version": "2021-07-27"}, {}, {}
            ),
        }
        super(SAMIService, self).__init__(self.service_info, self.api_info)

    def common_json_handler(self, api, body):
        params = dict()
        try:
            body = json.dumps(body)
            res = self.json(api, params, body)
            res_json = json.loads(res)
            return res_json
        except Exception as e:
            raise Exception(str(e))
