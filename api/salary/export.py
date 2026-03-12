"""Vercel Serverless Function — GET /api/salary/export.

Endpoint: GET /api/salary/export?month=YYYY-MM
Auth: Telegram initData (X-Telegram-Init-Data header)
Role: admin only

Trả về Excel file (.xlsx) bảng lương tháng cho toàn bộ nhân viên.
Dành cho admin/HR export báo cáo lương.
"""

import logging
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import base64

from services.auth_service import require_auth, json_api_response, handle_cors_preflight
from services.user_service import get_by_telegram_id
from services.salary_service import generate_salary_excel
from config.timezone import get_tz

logger = logging.getLogger(__name__)

# Validation bounds
_MIN_YEAR, _MAX_YEAR = 2020, 2100


class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler — GET /api/salary/export."""

    @require_auth
    def do_GET(self):
        """Export Excel bảng lương tháng (admin only)."""
        telegram_id = None
        try:
            telegram_id = self._telegram_user["id"]

            user = get_by_telegram_id(telegram_id)
            if not user:
                json_api_response(self, 404, {"ok": False, "error": "User not found"})
                return

            # Admin check
            if user.get("role") != "admin":
                json_api_response(self, 403, {"ok": False, "error": "Chỉ admin mới có quyền export bảng lương"})
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

            # Generate Excel
            excel_bytes = generate_salary_excel(month, year)
            filename = f"bang_luong_{year}_{month:02d}.xlsx"

            # Send file response
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.send_header("Content-Length", str(len(excel_bytes)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(excel_bytes)

        except Exception as e:
            logger.exception("GET /api/salary/export error — telegram_id=%s", telegram_id)
            json_api_response(self, 500, {"ok": False, "error": f"Internal error: {type(e).__name__}"})

    def do_OPTIONS(self):
        """CORS preflight."""
        handle_cors_preflight(self)
