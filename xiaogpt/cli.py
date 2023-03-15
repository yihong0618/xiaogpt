import argparse
import asyncio

from xiaogpt.config import Config
from xiaogpt.xiaogpt import MiGPT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--hardware",
        dest="hardware",
        help="小爱 hardware",
    )
    parser.add_argument(
        "--account",
        dest="account",
        help="xiaomi account",
    )
    parser.add_argument(
        "--password",
        dest="password",
        help="xiaomi password",
    )
    parser.add_argument(
        "--openai_key",
        dest="openai_key",
        help="openai api key",
    )
    parser.add_argument(
        "--cookie",
        dest="cookie",
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
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--use_gpt3",
        dest="bot",
        action="store_const",
        const="gpt3",
        help="if use openai gpt3 api",
    )
    group.add_argument(
        "--use_chatgpt_api",
        dest="bot",
        action="store_const",
        const="chatgptapi",
        help="if use openai chatgpt api",
    )
    group.add_argument(
        "--bot", dest="bot", help="bot type", choices=["gpt3", "chatgptapi"]
    )
    parser.add_argument(
        "--config",
        dest="config",
        help="config file path",
    )
    # args to change api_base
    parser.add_argument(
        "--api_base",
        dest="api_base",
        help="specify base url other than the OpenAI's official API address",
    )

    options = parser.parse_args()
    config = Config.from_options(options)

    miboy = MiGPT(config)
    asyncio.run(miboy.run_forever())


if __name__ == "__main__":
    main()
