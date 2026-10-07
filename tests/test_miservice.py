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

    async def test_startup_reuses_token_and_relogs_in_with_pass_token(self):
        token = {
            "deviceId": "test-device",
            "userId": "test-user",
            "passToken": "test-pass",
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

        async def security_token_service(account, location, nonce, ssecurity):
            return "refreshed-token"

        # token file state -> serviceTokens sent to mina, passTokens sent to login
        cases = {
            "missing": (["refreshed-token"], [None]),
            "valid": (["persisted-token"], []),
            "expired": (["persisted-token", "refreshed-token"], ["test-pass"]),
            "retry": (["refreshed-token"], ["test-pass"]),
        }
        for case, (service_tokens, pass_tokens) in cases.items():
            with self.subTest(case=case):
                self.bot.mi_token_home.unlink(missing_ok=True)
                if case != "missing":
                    self.bot.mi_token_home.write_text(json.dumps(token))
                statuses = iter([401, 200] if case == "expired" else [200])
                seen_tokens, logins = [], []

                def request(account, url, method, **kwargs):
                    seen_tokens.append(kwargs["cookies"]["serviceToken"])
                    return Response(next(statuses))

                async def service_login(account, uri, data=None):
                    logins.append(
                        (account.token["deviceId"], account.token.get("passToken"))
                    )
                    return {
                        "code": 0,
                        "userId": "test-user",
                        "passToken": "test-pass",
                        "location": "https://sts.example",
                        "nonce": "nonce",
                        "ssecurity": "security",
                    }

                with (
                    patch.object(MiAccount, "request", request),
                    patch.object(MiAccount, "_serviceLogin", service_login),
                    patch.object(
                        MiAccount, "_securityTokenService", security_token_service
                    ),
                ):
                    if case == "retry":
                        await self.bot._retry()
                    else:
                        await self.bot.init_all_data()

                self.assertEqual(seen_tokens, service_tokens)
                self.assertEqual([p for _, p in logins], pass_tokens)
                if case != "missing":
                    # relogin keeps the persisted device instead of a random one
                    self.assertTrue(all(d == "test-device" for d, _ in logins))
                persisted = json.loads(self.bot.mi_token_home.read_text())
                self.assertEqual(persisted["micoapi"][1], service_tokens[-1])
                self.assertEqual(
                    self.bot.get_cookie().get("serviceToken"), service_tokens[-1]
                )
                self.assertEqual(self.bot.device_id, "speaker")

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
