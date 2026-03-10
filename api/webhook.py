"""Vercel Serverless Function — Telegram Webhook endpoint.

Nhận POST từ Telegram Bot API, chuyển cho bot xử lý.
Deploy: https://pyng.vercel.app/api/webhook
"""

import json
import asyncio
from http.server import BaseHTTPRequestHandler

from telegram import Update

from bot.app import create_bot


# Tạo Application 1 lần (module-level) cho hiệu suất
_app = None


def _get_app():
    """Lazy init bot application."""
    global _app
    if _app is None:
        _app = create_bot()
    return _app


async def process_webhook(data: dict) -> None:
    """Parse và xử lý Telegram update."""
    app = _get_app()

    async with app:
        await app.process_update(
            Update.de_json(data=data, bot=app.bot)
        )


class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler cho Telegram webhook."""

    def do_POST(self):
        """Xử lý webhook POST từ Telegram."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)

            # Chạy async handler
            asyncio.run(process_webhook(data))

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())

        except Exception as e:
            print(f"[Webhook Error] {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode())

    def do_GET(self):
        """Health check endpoint."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "ok",
            "bot": "PyngBot",
            "message": "Webhook is running. Send POST to interact."
        }).encode())
