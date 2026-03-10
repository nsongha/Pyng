"""Vercel Serverless Function — Morning Reminder Cron.

Endpoint: POST /api/cron/morning
Trigger: GitHub Actions cron lúc 8:30 AM (UTC+7), thứ 2-6.

Gửi nhắc check-in cho tất cả active users chưa check-in hôm nay.
Tin nhắn kèm inline buttons theo BOT_FLOWS.md section 2.1.
"""

import asyncio
import logging
from http.server import BaseHTTPRequestHandler

logger = logging.getLogger(__name__)

from services.user_service import get_all_active_users
from services.checkin_service import has_checked_in_today
from services.cron_helpers import verify_cron_secret, send_telegram_message, json_response


def _build_morning_message(user_name: str) -> tuple[str, dict]:
    """Tạo tin nhắn nhắc check-in buổi sáng.

    Args:
        user_name: Tên hiển thị của user.

    Returns:
        tuple: (text, reply_markup) cho Telegram API.
    """
    text = (
        f"🌅 Chào buổi sáng, *{user_name}*!\n"
        f"Hôm nay bạn làm việc ở đâu?\n"
    )

    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "🏢 Tại văn phòng", "callback_data": "checkin_office"},
                {"text": "🏠 WFH hôm nay", "callback_data": "checkin_wfh"},
            ],
        ]
    }

    return text, reply_markup


async def _send_morning_reminders() -> dict:
    """Gửi nhắc check-in cho active users chưa check-in.

    Returns:
        dict: Summary kết quả gửi (sent, skipped, errors).
    """
    users = get_all_active_users()
    sent = 0
    skipped = 0
    errors = []

    for user in users:
        user_id = user.get("id")
        telegram_id = user.get("telegram_id")
        full_name = user.get("full_name", "bạn")

        if not telegram_id:
            continue

        # Skip nếu đã check-in hôm nay
        if has_checked_in_today(user_id):
            skipped += 1
            continue

        try:
            text, reply_markup = _build_morning_message(full_name)
            await send_telegram_message(
                chat_id=telegram_id,
                text=text,
                reply_markup=reply_markup,
            )
            sent += 1
        except Exception as e:
            errors.append({"user_id": user_id, "error": str(e)})

    return {
        "total_active": len(users),
        "sent": sent,
        "skipped_already_checked_in": skipped,
        "errors": errors,
    }


class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler — Morning reminder cron."""

    def do_POST(self):
        """Xử lý POST request từ GitHub Actions cron."""
        # 1. Verify CRON_SECRET
        auth = self.headers.get("Authorization")
        if not verify_cron_secret(auth):
            json_response(self, 401, {"error": "Unauthorized"})
            return

        try:
            # 2. Gửi nhắc nhở
            result = asyncio.run(_send_morning_reminders())
            json_response(self, 200, {"ok": True, "type": "morning", **result})
        except Exception as e:
            logger.exception("Cron morning error")
            json_response(self, 500, {"ok": False, "error": "Internal error"})

    def do_GET(self):
        """Health check."""
        json_response(self, 200, {
            "status": "ok",
            "endpoint": "morning-reminder",
            "message": "Send POST with Authorization header to trigger.",
        })
