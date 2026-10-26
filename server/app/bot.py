"""Long-polling bot; only replies to explicit private /start and /play."""

import os
import time
import httpx
from .config import BOT_TOKEN


class TelegramFailure(RuntimeError):
    def __init__(self, method, code):
        self.code = code
        reason = {
            401: "invalid or revoked BOT_TOKEN",
            404: "invalid BOT_TOKEN or Telegram method",
            409: "polling conflict: another bot process or active webhook",
            429: "Telegram rate limit",
        }.get(code, "Telegram request failed")
        super().__init__(f"{method}: code={code}; {reason}")


def request(client, method, payload=None):
    # Never log response descriptions, request URLs or transport exceptions:
    # those can contain credentials or user content.
    try:
        response = client.post(method, json=payload or {})
        data = response.json()
    except (httpx.HTTPError, ValueError):
        raise TelegramFailure(method, 503) from None
    if not isinstance(data, dict) or not data.get("ok"):
        code = data.get("error_code", response.status_code) if isinstance(data, dict) else response.status_code
        if not isinstance(code, int):
            code = response.status_code
        raise TelegramFailure(method, code)
    return data.get("result")


def initialize(client):
    me = request(client, "getMe")
    expected = os.environ.get("BOT_USERNAME", "Ironfrontwaw_bot")
    if me.get("username", "").lower() != expected.lower():
        raise RuntimeError("BOT_TOKEN belongs to a different bot; check BOT_USERNAME")
    webhook = request(client, "getWebhookInfo")
    if webhook.get("url"):
        raise RuntimeError("Active Telegram webhook prevents polling; migrate webhook before starting bot")
    print("Telegram identity verified; webhook absent", flush=True)


def main():
    url = os.environ["APP_URL"]
    offset = 0
    if not BOT_TOKEN or not url.startswith("https://"):
        raise RuntimeError("Configure BOT_TOKEN and HTTPS APP_URL")
    with httpx.Client(base_url=f"https://api.telegram.org/bot{BOT_TOKEN}/", timeout=40) as client:
        initialize(client)
        ready = False
        while True:
            try:
                updates = request(client, "getUpdates", {
                    "offset": offset, "timeout": 25, "allowed_updates": ["message"]
                })
                if not ready:
                    print("Telegram polling ready", flush=True)
                    ready = True
                for update in updates:
                    message = update.get("message", {})
                    if (message.get("text", "").split(" ")[0] in ["/start", "/play"]
                            and message.get("chat", {}).get("type") == "private"):
                        try:
                            request(client, "sendMessage", {
                                "chat_id": message["chat"]["id"],
                                "text": "IRON FRONT · WORLD AT WAR\nПострой базу. Подготовь отряд. Начни первую операцию.",
                                "reply_markup": {"inline_keyboard": [[{
                                    "text": "Открыть IRON FRONT", "web_app": {"url": url}
                                }]]},
                            })
                        except TelegramFailure as error:
                            if error.code != 403:  # A blocked bot must not stall all updates.
                                raise
                    offset = update["update_id"] + 1
            except TelegramFailure as error:
                if error.code != 429 and error.code < 500:
                    raise
                print(str(error), flush=True)
                time.sleep(30)


if __name__ == "__main__":
    main()
