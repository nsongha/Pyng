"""Vercel Serverless Function — Evening Reminder Cron.

Endpoint: POST /api/cron/evening
Trigger: GitHub Actions cron lúc 17:45 PM (UTC+7), thứ 2-6.

Gửi nhắc check-out cho users đã check-in nhưng chưa check-out hôm nay.
"""

import asyncio
from http.server import BaseHTTPRequestHandler

from services.user_service import get_all_active_users
from services.checkin_service import has_checked_in_today, get_today_checkin
from api.cron._helpers import verify_cron_secret, send_telegram_message, json_response


def _build_evening_message(user_name: str) -> tuple[str, dict]:
    """Tạo tin nhắn nhắc check-out buổi chiều.

    Args:
        user_name: Tên hiển thị của user.

    Returns:
        tuple: (text, reply_markup) cho Telegram API.
    """
    text = (
        f"🌆 Hết giờ rồi, *{user_name}*!\n"
        f"Đừng quên check-out nhé."
    )

    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "🚪 CHECK OUT", "callback_data": "checkout"},
            ],
        ]
    }

    return text, reply_markup


async def _send_evening_reminders() -> dict:
    """Gửi nhắc check-out cho users đã check-in nhưng chưa checkout.

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

        # Skip nếu chưa check-in hôm nay
        if not has_checked_in_today(user_id):
            skipped += 1
            continue

        # Skip nếu đã check-out rồi
        checkout = get_today_checkin(user_id, "out")
        if checkout is not None:
            skipped += 1
            continue

        try:
            text, reply_markup = _build_evening_message(full_name)
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
        "skipped_no_checkin_or_already_out": skipped,
        "errors": errors,
    }


class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler — Evening reminder cron."""

    def do_POST(self):
        """Xử lý POST request từ GitHub Actions cron."""
        # 1. Verify CRON_SECRET
        auth = self.headers.get("Authorization")
        if not verify_cron_secret(auth):
            json_response(self, 401, {"error": "Unauthorized"})
            return

        try:
            # 2. Gửi nhắc nhở
            result = asyncio.run(_send_evening_reminders())
            json_response(self, 200, {"ok": True, "type": "evening", **result})
        except Exception as e:
            print(f"[Cron Evening Error] {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            json_response(self, 500, {"ok": False, "error": str(e)})

    def do_GET(self):
        """Health check."""
        json_response(self, 200, {
            "status": "ok",
            "endpoint": "evening-reminder",
            "message": "Send POST with Authorization header to trigger.",
        })
