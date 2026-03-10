"""Vercel Serverless Function — Telegram Webhook endpoint.

Nhận POST từ Telegram Bot API, chuyển cho bot xử lý.
Deploy: https://pyng.vercel.app/api/webhook
"""

import json
import asyncio
from http.server import BaseHTTPRequestHandler

from telegram import Update

from bot.app import create_bot


# Khởi tạo bot 1 lần (reuse giữa các invocations trên Vercel)
app = create_bot()


class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler cho Telegram webhook."""

    def do_POST(self):
        """Xử lý webhook POST từ Telegram."""
        try:
            # Đọc body
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)

            # Parse Update và xử lý
            update = Update.de_json(data=data, bot=app.bot)
            asyncio.run(app.process_update(update))

            # Trả về 200 OK
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())

        except Exception as e:
            # Log lỗi nhưng vẫn trả 200 (tránh Telegram retry liên tục)
            print(f"[Webhook Error] {e}")
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
