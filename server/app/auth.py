import hashlib, hmac, json, time
from urllib.parse import parse_qsl
from fastapi import HTTPException


def validate_init_data(raw, token, now=None):
    now = int(time.time()) if now is None else now
    try:
        pairs = parse_qsl(raw, keep_blank_values=True, strict_parsing=True)
        if len({k for k, v in pairs}) != len(pairs):
            raise ValueError()
        data = dict(pairs)
        supplied = data.pop("hash")
        secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
        expected = hmac.new(
            secret,
            "\n".join(f"{k}={v}" for k, v in sorted(data.items())).encode(),
            hashlib.sha256,
        ).hexdigest()
        if not token or not hmac.compare_digest(expected, supplied):
            raise ValueError()
        age = now - int(data["auth_date"])
        if age < -30 or age > 300:
            raise ValueError()
        user = json.loads(data["user"])
        if type(user["id"]) is not int or user["id"] <= 0:
            raise ValueError()
        return user
    except (ValueError, KeyError, TypeError):
        raise HTTPException(401, "Недействительная или устаревшая авторизация Telegram")


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()
