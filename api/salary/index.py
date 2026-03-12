"""Vercel Serverless Function — GET /api/salary.

Endpoint: GET /api/salary?month=YYYY-MM
Auth: Telegram initData (X-Telegram-Init-Data header)

Trả về salary summary cho user hiện tại:
    - basic_salary: lương cơ bản
    - ot_allowance: phụ cấp OT
    - late_deductions: khấu trừ đi muộn
    - unpaid_leave_deduction: khấu trừ nghỉ không lương
    - net_salary: lương ròng
"""

import logging
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from services.auth_service import require_auth, json_api_response, handle_cors_preflight
from services.user_service import get_by_telegram_id
from services.salary_service import calculate_monthly_salary
from config.timezone import get_tz

logger = logging.getLogger(__name__)

# Validation bounds
_MIN_YEAR, _MAX_YEAR = 2020, 2100


class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler — GET /api/salary."""

    @require_auth
    def do_GET(self):
        """Trả về salary summary cho tháng được chọn."""
        telegram_id = None
        try:
            telegram_id = self._telegram_user["id"]

            user = get_by_telegram_id(telegram_id)
            if not user:
                json_api_response(self, 404, {"ok": False, "error": "User not found"})
                return

            # Parse month param (YYYY-MM)
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
                    json_api_response(self, 400, {"ok": False, "error": "Invalid month format. Use YYYY-MM"})
                    return
            else:
                year = now.year
                month = now.month

            # Validate bounds
            if month < 1 or month > 12 or year < _MIN_YEAR or year > _MAX_YEAR:
                json_api_response(self, 400, {"ok": False, "error": "Invalid month/year"})
                return

            salary_data = calculate_monthly_salary(user["id"], month, year)

            json_api_response(self, 200, {
                "ok": True,
                "month": f"{year}-{month:02d}",
                "salary": salary_data,
            })

        except Exception as e:
            logger.exception("GET /api/salary error — telegram_id=%s", telegram_id)
            json_api_response(self, 500, {"ok": False, "error": f"Internal error: {type(e).__name__}"})

    def do_OPTIONS(self):
        """CORS preflight."""
        handle_cors_preflight(self)
