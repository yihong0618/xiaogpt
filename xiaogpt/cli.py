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
        "--glm_key",
        dest="glm_key",
        help="chatglm api key",
    )
    parser.add_argument(
        "--gemini_key",
        dest="gemini_key",
        help="gemini api key",
    )
    parser.add_argument(
        "--qwen_key",
        dest="qwen_key",
        help="Alibaba Qwen api key",
    )
    parser.add_argument(
        "--serpapi_api_key",
        dest="serpapi_api_key",
        help="serp api key see https://serpapi.com/",
    )
    parser.add_argument(
        "--proxy",
        dest="proxy",
        help="http proxy url like http://localhost:8080",
    )
    parser.add_argument(
        "--cookie",
        dest="cookie",
        help="xiaomi cookie",
    )
    parser.add_argument(
        "--stream",
        dest="stream",
        action="store_true",
        default=None,
        help="GPT stream mode",
    )
    parser.add_argument(
        "--use_command",
        dest="use_command",
        action="store_true",
        default=None,
        help="use command to tts",
    )
    parser.add_argument(
        "--mute_xiaoai",
        dest="mute_xiaoai",
        action="store_true",
        default=None,
        help="try to mute xiaoai answer",
    )
    parser.add_argument(
        "--verbose",
        dest="verbose",
        action="store_true",
        default=None,
        help="show info",
    )
    parser.add_argument(
        "--tts",
        help="TTS provider",
        choices=["mi", "edge", "openai", "azure", "google", "baidu", "volc"],
    )
    bot_group = parser.add_mutually_exclusive_group()
    bot_group.add_argument(
        "--use_chatgpt_api",
        dest="bot",
        action="store_const",
        const="chatgptapi",
        help="if use openai chatgpt api",
    )
    bot_group.add_argument(
        "--use_langchain",
        dest="bot",
        action="store_const",
        const="langchain",
        help="if use langchain",
    )
    bot_group.add_argument(
        "--use_newbing",
        dest="bot",
        action="store_const",
        const="newbing",
        help="if use newbing",
    )
    bot_group.add_argument(
        "--use_glm",
        dest="bot",
        action="store_const",
        const="glm",
        help="if use chatglm",
    )
    bot_group.add_argument(
        "--use_qwen",
        dest="bot",
        action="store_const",
        const="qwen",
        help="if use qwen",
    )
    bot_group.add_argument(
        "--use_gemini",
        dest="bot",
        action="store_const",
        const="gemini",
        help="if use gemini",
    )
    parser.add_argument(
        "--bing_cookie_path",
        dest="bing_cookie_path",
        help="new bing cookies path if use new bing",
    )
    bot_group.add_argument(
        "--bot",
        dest="bot",
        help="bot type",
        choices=[
            "chatgptapi",
            "newbing",
            "glm",
            "gemini",
            "langchain",
            "qwen",
        ],
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

    parser.add_argument(
        "--deployment_id",
        dest="deployment_id",
        help="specify deployment id, only used when api_base points to azure",
    )

    options = parser.parse_args()
    config = Config.from_options(options)

    async def main(config: Config) -> None:
        miboy = MiGPT(config)
        try:
            await miboy.run_forever()
        finally:
            await miboy.close()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(config))


if __name__ == "__main__":
    main()
