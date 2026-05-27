"""
Shared Telegram WebApp initData verification.
Imported by both game.py and user.py — avoids code duplication.
"""
import hashlib
import hmac
import json
import os
from urllib.parse import unquote


def verify_telegram_init_data(init_data: str) -> dict | None:
    """
    Verifies Telegram WebApp initData using HMAC-SHA256.
    Returns parsed user dict if valid, None if invalid.
    Spec: https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app
    """
    bot_token = os.getenv("BOT_TOKEN", "")
    if not bot_token or not init_data:
        return None

    try:
        params = {}
        for part in init_data.split("&"):
            if "=" in part:
                k, v = part.split("=", 1)
                params[unquote(k)] = unquote(v)

        received_hash = params.pop("hash", None)
        if not received_hash:
            return None

        # Build data-check-string: sorted key=value pairs joined by \n
        data_check = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))

        # secret_key = HMAC_SHA256(key="WebAppData", msg=bot_token)
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        computed   = hmac.new(secret_key, data_check.encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(computed, received_hash):
            return None

        return json.loads(params.get("user", "{}"))
    except Exception:
        return None


def get_verified_user_id(init_data: str | None) -> str | None:
    """Returns verified Telegram user_id as string, or None if invalid/missing."""
    if not init_data:
        return None
    user = verify_telegram_init_data(init_data)
    if user and user.get("id"):
        return str(user["id"])
    return None
