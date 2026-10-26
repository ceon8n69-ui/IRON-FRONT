"""Long-polling bot process. No messages except explicit /start responses."""

import os, time, httpx
from .config import BOT_TOKEN


def main():
    url = os.environ["APP_URL"]
    offset = 0
    if not BOT_TOKEN or not url.startswith("https://"):
        raise RuntimeError("Configure BOT_TOKEN and HTTPS APP_URL")
    with httpx.Client(
        base_url=f"https://api.telegram.org/bot{BOT_TOKEN}/", timeout=40
    ) as client:
        while True:
            response = client.post(
                "getUpdates",
                json={"offset": offset, "timeout": 25, "allowed_updates": ["message"]},
            ).json()
            if not response.get("ok"):
                raise RuntimeError(
                    "Telegram polling failed; check token/webhook configuration"
                )
            for update in response["result"]:
                message = update.get("message", {})
                if (
                    message.get("text", "").split(" ")[0] in ["/start", "/play"]
                    and message.get("chat", {}).get("type") == "private"
                ):
                    sent = client.post(
                        "sendMessage",
                        json={
                            "chat_id": message["chat"]["id"],
                            "text": "IRON FRONT · WORLD AT WAR\nПострой базу. Подготовь отряд. Начни первую операцию.",
                            "reply_markup": {
                                "inline_keyboard": [
                                    [
                                        {
                                            "text": "Открыть IRON FRONT",
                                            "web_app": {"url": url},
                                        }
                                    ]
                                ]
                            },
                        },
                    ).json()
                    if not sent.get("ok"):
                        raise RuntimeError("Telegram send failed")
                offset = update["update_id"] + 1


if __name__ == "__main__":
    main()
