import unittest
from unittest.mock import patch
import httpx
from app.bot import initialize, request, TelegramFailure


class BotTests(unittest.TestCase):
    def client(self, handler):
        return httpx.Client(base_url="https://api.telegram.org/botPRIVATE/", transport=httpx.MockTransport(handler))

    def test_invalid_token_sanitized(self):
        with self.client(lambda r: httpx.Response(401, json={"ok": False, "error_code": 401, "description": "PRIVATE"})) as client:
            with self.assertRaises(TelegramFailure) as error:
                request(client, "getMe")
        self.assertIn("invalid or revoked", str(error.exception))
        self.assertNotIn("PRIVATE", str(error.exception))

    def test_transport_sanitized(self):
        def fail(req):
            raise httpx.ConnectError(str(req.url))
        with self.client(fail) as client:
            with self.assertRaises(TelegramFailure) as error:
                request(client, "getMe")
        self.assertEqual(error.exception.code, 503)
        self.assertNotIn("PRIVATE", str(error.exception))

    def test_wrong_bot_rejected(self):
        with self.client(lambda r: httpx.Response(200, json={"ok": True, "result": {"username": "other_bot"}})) as client:
            with self.assertRaisesRegex(RuntimeError, "different bot"):
                initialize(client)

    def test_webhook_not_deleted(self):
        calls = []
        def handler(req):
            calls.append(req.url.path.split('/')[-1])
            result = {"username": "Ironfrontwaw_bot"} if calls[-1] == "getMe" else {"url": "https://private.example/hook"}
            return httpx.Response(200, json={"ok": True, "result": result})
        with self.client(handler) as client:
            with self.assertRaisesRegex(RuntimeError, "Active Telegram webhook"):
                initialize(client)
        self.assertEqual(calls, ["getMe", "getWebhookInfo"])

    def test_valid_identity(self):
        def handler(req):
            result = {"username": "Ironfrontwaw_bot"} if req.url.path.endswith("getMe") else {"url": ""}
            return httpx.Response(200, json={"ok": True, "result": result})
        with self.client(handler) as client, patch('builtins.print'):
            initialize(client)

    def test_polling_conflict(self):
        with self.client(lambda r: httpx.Response(409, json={"ok": False, "error_code": 409})) as client:
            with self.assertRaisesRegex(TelegramFailure, "polling conflict"):
                request(client, "getUpdates")
