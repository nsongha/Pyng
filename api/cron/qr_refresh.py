"""Vercel Serverless Function — QR Refresh Cron.

Endpoint: POST /api/cron/qr_refresh
Trigger: GitHub Actions cron mỗi 5 phút (giờ làm việc, weekday).

Cleanup QR expired + tạo QR mới cho office active.
"""

import asyncio
import logging
from datetime import datetime
from http.server import BaseHTTPRequestHandler

logger = logging.getLogger(__name__)

from services.qr_service import cleanup_expired_qr, create_qr_session, get_current_qr
from services.office_service import get_active_office
from services.cron_helpers import verify_cron_secret, json_response
from config.timezone import get_tz
from config.settings import WORK_START, WORK_END


def _is_work_hours() -> bool:
    """Kiểm tra hiện tại có trong giờ làm việc không.

    Returns:
        bool: True nếu weekday và trong khoảng WORK_START - WORK_END.
    """
    tz = get_tz()
    now = datetime.now(tz)

    # Chỉ weekday (0=Monday, 6=Sunday)
    if now.weekday() >= 5:
        return False

    # Parse giờ làm việc
    start_h, start_m = map(int, WORK_START.split(":"))
    end_h, end_m = map(int, WORK_END.split(":"))

    start_minutes = start_h * 60 + start_m
    end_minutes = end_h * 60 + end_m
    current_minutes = now.hour * 60 + now.minute

    # Mở rộng thêm 30 phút trước/sau giờ làm
    return (start_minutes - 30) <= current_minutes <= (end_minutes + 30)


class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler — QR refresh cron."""

    def do_POST(self):
        """Xử lý POST request từ GitHub Actions cron."""
        # 1. Verify CRON_SECRET
        auth = self.headers.get("Authorization")
        if not verify_cron_secret(auth):
            json_response(self, 401, {"error": "Unauthorized"})
            return

        try:
            # 2. Kiểm tra giờ làm việc
            if not _is_work_hours():
                json_response(self, 200, {
                    "ok": True,
                    "action": "skipped",
                    "reason": "Ngoài giờ làm việc",
                })
                return

            # 3. Cleanup expired QR
            deleted = cleanup_expired_qr()

            # 4. Đảm bảo có QR active
            office = get_active_office()
            if not office:
                json_response(self, 200, {
                    "ok": True,
                    "action": "skipped",
                    "reason": "Không có office active",
                })
                return

            qr_session = get_current_qr(office["id"])

            json_response(self, 200, {
                "ok": True,
                "action": "refreshed",
                "expired_cleaned": len(deleted) if isinstance(deleted, list) else 0,
                "current_token": qr_session["token"],
                "expire_at": qr_session["expire_at"],
            })

        except Exception as e:
            logger.exception("QR refresh cron error")
            json_response(self, 500, {"ok": False, "error": "Internal error"})

    def do_GET(self):
        """Health check."""
        json_response(self, 200, {
            "status": "ok",
            "endpoint": "qr-refresh",
            "message": "Send POST with Authorization header to trigger.",
        })
