import argparse
import asyncio
import json
import os
from os import environ as env

from xiaogpt.xiaogpt import MiGPT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--hardware",
        dest="hardware",
        type=str,
        default="",
        help="小爱 hardware",
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
        "--openai_key",
        dest="openai_key",
        type=str,
        default="",
        help="openai api key",
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
    parser.add_argument(
        "--verbose",
        dest="verbose",
        action="store_true",
        help="show info",
    )
    parser.add_argument(
        "--use_gpt3",
        dest="use_gpt3",
        action="store_true",
        help="if use openai gpt3 api",
    )
    parser.add_argument(
        "--use_chatgpt_api",
        dest="use_chatgpt_api",
        action="store_true",
        help="if use openai chatgpt api",
    )
    parser.add_argument(
        "--config",
        dest="config",
        type=str,
        default="",
        help="config file path",
    )
    # args to change api_base
    parser.add_argument(
        "--api_base",
        dest="api_base",
        type=str,
        help="specify base url other than the OpenAI's official API address",
    )

    options = parser.parse_args()

    key_word_list = []
    prompt = ""
    if options.config:
        config = {}
        if os.path.exists(options.config):
            with open(options.config, "r") as f:
                config = json.load(f)
        else:
            raise Exception(f"{options.config} doesn't exist")

        # update options with config
        for key, value in config.items():
            if not getattr(options, key, None):
                setattr(options, key, value)
            if key == "keyword":
                if not isinstance(value, list):
                    value = [value]
                key_word_list = [kw for kw in value if kw]
            elif key == "prompt":
                prompt = value

    # if set
    mi_user = options.account or env.get("MI_USER")
    mi_pass = options.password or env.get("MI_PASS")
    OPENAI_API_KEY = options.openai_key or env.get("OPENAI_API_KEY")
    if options.use_gpt3:
        if not OPENAI_API_KEY:
            raise Exception("Use gpt-3 api need openai API key, please google how to")
    if options.use_chatgpt_api:
        if not OPENAI_API_KEY:
            raise Exception("Use chatgpt api need openai API key, please google how to")

    miboy = MiGPT(
        options.hardware,
        mi_user,
        mi_pass,
        OPENAI_API_KEY,
        options.cookie,
        options.use_command,
        options.mute_xiaoai,
        options.use_gpt3,
        options.use_chatgpt_api,
        options.api_base,  # change api_base for issue #101
        options.verbose,
    )
    if key_word_list:
        miboy.key_word = key_word_list
    if prompt:
        miboy.prompt = prompt
    asyncio.run(miboy.run_forever())


if __name__ == "__main__":
    main()
