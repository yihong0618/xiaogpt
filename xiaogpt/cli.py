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
        "--model",
        dest="model",
        help="LLM model in the form of `provider:model`, e.g. openai:gpt-4o-mini",
    )
    parser.add_argument(
        "--api_key",
        "--openai_key",
        dest="api_key",
        help="API key of the model provider",
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
        "--volc_access_key", dest="volc_access_key", help="Volcengine access key"
    )
    parser.add_argument(
        "--volc_secret_key", dest="volc_secret_key", help="Volcengine secret key"
    )
    # for fish tts
    parser.add_argument("--fish_api_key", dest="fish_api_key", help="fish api key")
    parser.add_argument(
        "--fish_voice_key", dest="fish_voice_key", help="fish voice key"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        dest="verbose",
        action="count",
        default=0,
        help="show info",
    )
    parser.add_argument(
        "--tts",
        help="TTS provider",
        choices=["mi", "edge", "openai", "azure", "google", "baidu", "volc", "fish"],
    )
    parser.add_argument(
        "--config",
        dest="config",
        help="config file path",
    )
    parser.add_argument(
        "--api_base",
        dest="api_base",
        help="specify base url other than the provider's default API address",
    )
    parser.add_argument(
        "--api_format",
        dest="api_format",
        help='chat API format, e.g. "chat" for OpenAI-compatible services',
    )

    options = parser.parse_args()
    config = Config.from_options(options)

    async def main(config: Config) -> None:
        miboy = MiGPT(config)
        try:
            await miboy.run_forever()
        finally:
            await miboy.close()

    asyncio.run(main(config))


if __name__ == "__main__":
    main()
