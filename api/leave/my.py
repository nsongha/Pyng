"""Vercel Serverless Function — GET /api/leave/my.

Endpoint: GET /api/leave/my?year=2026
Auth: Telegram initData (X-Telegram-Init-Data header)

Trả về danh sách leave requests + balance cho user hiện tại.
"""

import logging
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from services.auth_service import require_auth, json_api_response, handle_cors_preflight
from services.user_service import get_by_telegram_id
from services.leave_service import get_user_leaves, get_remaining_leave_days
from config.timezone import get_tz

logger = logging.getLogger(__name__)


class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler — GET /api/leave/my."""

    @require_auth
    def do_GET(self):
        """Trả về leaves list + balance."""
        try:
            telegram_id = self._telegram_user["id"]

            user = get_by_telegram_id(telegram_id)
            if not user:
                json_api_response(self, 404, {"error": "User not found"})
                return

            # Parse year param
            parsed_url = urlparse(self.path)
            params = parse_qs(parsed_url.query)
            year_str = params.get("year", [None])[0]

            tz = get_tz()
            now = datetime.now(tz)

            if year_str:
                try:
                    year = int(year_str)
                except ValueError:
                    json_api_response(self, 400, {"error": "Invalid year format"})
                    return
            else:
                year = now.year

            # Lấy leaves list
            leaves = get_user_leaves(user["id"], year=year)

            # Lấy balance
            balance = get_remaining_leave_days(user["id"])

            json_api_response(self, 200, {
                "ok": True,
                "year": year,
                "leaves": leaves,
                "balance": balance,
            })

        except Exception:
            logger.exception("GET /api/leave/my error")
            json_api_response(self, 500, {"ok": False, "error": "Internal error"})

    def do_OPTIONS(self):
        """CORS preflight."""
        handle_cors_preflight(self)
