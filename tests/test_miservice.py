"""Run offline with: python -m unittest discover -s tests -v"""

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from miservice import MiAccount
from xiaogpt.config import Config
from xiaogpt.tts.base import TTS
from xiaogpt.xiaogpt import MiGPT


class MiServiceMigrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.bot = MiGPT(
            Config(
                account="test",
                password="test",
                openai_key="test",
                hardware="S12A",
                mi_did="123",
                mute_xiaoai=True,
            )
        )
        self.bot.mi_token_home = Path(self.temp.name) / ".mi.token"

    async def asyncTearDown(self):
        await self.bot.close()
        self.temp.cleanup()

    async def test_startup_reuses_token_and_service_reauthenticates(self):
        token = {
            "userId": "test-user",
            "deviceId": "test-device",
            "micoapi": ["security", "persisted-token"],
        }
        devices = [{"deviceID": "speaker", "miotDID": "123", "hardware": "S12A"}]

        class Response:
            def __init__(self, status):
                self.status = status

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def json(self, **kwargs):
                return {"code": 0, "data": devices}

            async def text(self):
                return "expired"

        for expired in ("missing", False, True):
            with self.subTest(expired=expired):
                if expired != "missing":
                    self.bot.mi_token_home.write_text(json.dumps(token))
                statuses = iter([401, 200] if expired is True else [200])
                seen_tokens = []

                def request(account, url, method, **kwargs):
                    seen_tokens.append(kwargs["cookies"]["serviceToken"])
                    return Response(next(statuses))

                async def login(account, sid):
                    account.token = {**token, sid: ["security", "refreshed-token"]}
                    await account.token_store.save_token(account.token)
                    return True

                with (
                    patch.object(MiAccount, "request", request),
                    patch.object(
                        MiAccount, "login", autospec=True, side_effect=login
                    ) as authenticate,
                ):
                    await self.bot.init_all_data()
                    self.assertEqual(
                        authenticate.await_count, int(expired is not False)
                    )
                    self.assertEqual(
                        seen_tokens,
                        (
                            ["persisted-token", "refreshed-token"]
                            if expired is True
                            else (
                                ["refreshed-token"]
                                if expired == "missing"
                                else ["persisted-token"]
                            )
                        ),
                    )
                    self.assertEqual(self.bot.device_id, "speaker")
                    self.assertIn(
                        "refreshed-token" if expired else "persisted-token",
                        self.bot.mi_token_home.read_text(),
                    )

    async def test_official_playback_status_for_both_callers(self):
        for response, playing in (
            ({"status": 1}, True),
            ({"status": 0}, False),
            (None, False),
        ):
            self.bot.mina_service = SimpleNamespace(
                player_get_status=AsyncMock(return_value=response)
            )
            self.assertEqual(await self.bot.get_if_xiaoai_is_playing(), playing)
            self.assertEqual(await TTS.get_if_xiaoai_is_playing(self.bot), playing)

    async def test_pause_still_checks_playback_status(self):
        for status in (0, 1):
            self.bot.mina_service = SimpleNamespace(
                player_get_status=AsyncMock(return_value={"status": status}),
                player_pause=AsyncMock(),
            )
            await self.bot.stop_if_xiaoai_is_playing()
            self.bot.mina_service.player_get_status.assert_awaited_once()
            self.assertEqual(self.bot.mina_service.player_pause.await_count, status)

    async def test_tts_waits_until_playback_finishes(self):
        from xiaogpt.tts.mi import MiTTS

        self.bot.mina_service = SimpleNamespace(
            account=None,
            player_get_status=AsyncMock(side_effect=[{"status": 1}, {"status": 0}]),
        )
        tts = MiTTS(self.bot.mina_service, "speaker", self.bot.config)
        with patch("xiaogpt.tts.base.asyncio.sleep", new_callable=AsyncMock) as sleep:
            await tts.wait_for_duration(0)
        self.assertEqual(tts.mina_service.player_get_status.await_count, 2)
        self.assertEqual([call.args[0] for call in sleep.await_args_list], [0, 1])
        self.assertEqual(
            (self.bot.config.tts_command, self.bot.config.wakeup_command),
            ("5-1", "5-5"),
        )
