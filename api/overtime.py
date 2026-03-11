"""Vercel Serverless Function — GET /api/overtime.

Endpoint: GET /api/overtime?month=2026-03
Auth: Telegram initData (X-Telegram-Init-Data header)

Trả về overtime data cho user hiện tại:
    - total_minutes: tổng phút OT tháng
    - total_days: số ngày có OT
    - sessions: [{date, minutes, checkout_time}]
"""

import logging
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from services.auth_service import require_auth, json_api_response, handle_cors_preflight
from services.user_service import get_by_telegram_id
from services.overtime_service import get_monthly_overtime
from config.timezone import get_tz

logger = logging.getLogger(__name__)

# Validation bounds
_MIN_YEAR, _MAX_YEAR = 2020, 2100


class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler — GET /api/overtime."""

    @require_auth
    def do_GET(self):
        """Trả về overtime data cho tháng được chọn."""
        try:
            telegram_id = self._telegram_user["id"]

            user = get_by_telegram_id(telegram_id)
            if not user:
                json_api_response(self, 404, {"error": "User not found"})
                return

            # Parse month param
            parsed_url = urlparse(self.path)
            params = parse_qs(parsed_url.query)
            month_str = params.get("month", [None])[0]

            tz = get_tz()
            now = datetime.now(tz)

            if month_str:
                try:
                    parts = month_str.split("-")
                    year = int(parts[0])
                    month = int(parts[1])
                except (ValueError, IndexError):
                    json_api_response(self, 400, {"error": "Invalid month format. Use YYYY-MM"})
                    return
            else:
                year = now.year
                month = now.month

            # Validate bounds
            if month < 1 or month > 12 or year < _MIN_YEAR or year > _MAX_YEAR:
                json_api_response(self, 400, {"error": "Invalid month/year"})
                return

            ot_data = get_monthly_overtime(user["id"], month, year)

            json_api_response(self, 200, {
                "ok": True,
                "month": f"{year}-{month:02d}",
                **ot_data,
            })

        except Exception:
            logger.exception("GET /api/overtime error")
            json_api_response(self, 500, {"ok": False, "error": "Internal error"})

    def do_OPTIONS(self):
        """CORS preflight."""
        handle_cors_preflight(self)
