"""Vercel Serverless Function — Daily Report Cron.

Endpoint: POST /api/cron/daily_report
Trigger: GitHub Actions cron lúc 9:15 AM (UTC+7), thứ 2-6.

Gửi báo cáo tổng hợp hàng ngày vào admin group.
Format: có mặt, WFH, vắng, muộn, nghỉ phép + danh sách chi tiết.
"""

import asyncio
import logging
from http.server import BaseHTTPRequestHandler

logger = logging.getLogger(__name__)

from services.report_service import generate_daily_text_report
from services.cron_helpers import verify_cron_secret, send_telegram_message, json_response
from config.settings import ADMIN_GROUP_ID


async def _send_daily_report() -> dict:
    """Tạo và gửi daily report vào admin group.

    Returns:
        dict: Summary kết quả gửi.
    """
    if not ADMIN_GROUP_ID:
        return {"ok": False, "error": "ADMIN_GROUP_ID not configured"}

    # Tạo report text từ report_service
    report_text = generate_daily_text_report()

    # Gửi vào admin group
    result = await send_telegram_message(
        chat_id=ADMIN_GROUP_ID,
        text=report_text,
    )

    return {
        "ok": True,
        "chat_id": ADMIN_GROUP_ID,
        "telegram_response": result,
    }


class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler — Daily report cron."""

    def do_POST(self):
        """Xử lý POST request từ GitHub Actions cron."""
        # 1. Verify CRON_SECRET
        auth = self.headers.get("Authorization")
        if not verify_cron_secret(auth):
            json_response(self, 401, {"error": "Unauthorized"})
            return

        try:
            # 2. Tạo và gửi report
            result = asyncio.run(_send_daily_report())
            json_response(self, 200, {"type": "daily_report", **result})
        except Exception as e:
            logger.exception("Cron daily_report error")
            json_response(self, 500, {"ok": False, "error": "Internal error"})

    def do_GET(self):
        """Health check."""
        json_response(self, 200, {
            "status": "ok",
            "endpoint": "daily-report",
            "message": "Send POST with Authorization header to trigger.",
        })
