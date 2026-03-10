"""Pyng — Shared utilities cho cron endpoints.

Cung cấp:
- verify_cron_secret: Xác thực CRON_SECRET từ Authorization header.
- send_telegram_message: Gửi tin nhắn qua Telegram Bot API (httpx).
- json_response: Helper trả HTTP JSON response.
"""

import json
from http.server import BaseHTTPRequestHandler

import httpx

from config.settings import CRON_SECRET, TELEGRAM_BOT_TOKEN

# Telegram Bot API base URL
_TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def verify_cron_secret(authorization: str | None) -> bool:
    """Kiểm tra CRON_SECRET từ Authorization header.

    Expected format: "Bearer <CRON_SECRET>"

    Args:
        authorization: Giá trị header Authorization.

    Returns:
        bool: True nếu secret hợp lệ.
    """
    if not CRON_SECRET:
        return False
    if not authorization:
        return False

    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0] != "Bearer":
        return False

    return parts[1] == CRON_SECRET


async def send_telegram_message(
    chat_id: int,
    text: str,
    *,
    reply_markup: dict | None = None,
) -> dict:
    """Gửi tin nhắn qua Telegram Bot API.

    Dùng httpx (lightweight) thay vì init full bot Application.

    Args:
        chat_id: Telegram chat ID.
        text: Nội dung tin nhắn (Markdown).
        reply_markup: Optional inline keyboard markup.

    Returns:
        dict: Telegram API response.
    """
    payload: dict = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            f"{_TELEGRAM_API}/sendMessage",
            json=payload,
        )
        return response.json()


def json_response(
    handler: BaseHTTPRequestHandler,
    status: int,
    data: dict,
) -> None:
    """Gửi JSON response từ Vercel serverless handler.

    Args:
        handler: BaseHTTPRequestHandler instance.
        status: HTTP status code.
        data: Dict sẽ serialize thành JSON.
    """
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.end_headers()
    handler.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
