"""Vercel Serverless Function — GET /api/me.

Endpoint: GET /api/me
Auth: Telegram initData (X-Telegram-Init-Data header)

Trả về user dashboard data:
    - user: thông tin cá nhân
    - gamification: điểm, streak, rank
    - checkin_stats: tóm tắt check-in tháng này
    - leave_balance: ngày phép còn lại
"""

import logging
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler

from services.auth_service import require_auth, json_api_response, handle_cors_preflight
from services.user_service import get_by_telegram_id
from services.gamification_service import get_user_stats
from services.leave_service import get_remaining_leave_days
from db import client as db
from config.timezone import get_tz

logger = logging.getLogger(__name__)


def _get_checkin_stats_this_month(user_id: int) -> dict:
    """Tính check-in summary tháng này.

    Args:
        user_id: ID user (bảng users.id).

    Returns:
        dict: {total, ontime, late, wfh}
    """
    tz = get_tz()
    now = datetime.now(tz)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if now.month == 12:
        end = start.replace(year=now.year + 1, month=1)
    else:
        end = start.replace(month=now.month + 1)

    rows = db.select(
        "checkins",
        columns="id,method,is_ontime",
        filters={
            "user_id": user_id,
            "type": "in",
            "checked_at.gte": start.isoformat(),
            "checked_at.lt": end.isoformat(),
        },
    )

    total = len(rows)
    ontime = sum(1 for r in rows if r.get("is_ontime"))
    wfh = sum(1 for r in rows if r.get("method") == "wfh")
    late = total - ontime - wfh

    return {
        "total": total,
        "ontime": ontime,
        "late": max(0, late),
        "wfh": wfh,
    }


class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler — GET /api/me."""

    @require_auth
    def do_GET(self):
        """Trả về user dashboard data."""
        try:
            telegram_id = self._telegram_user["id"]

            # 1. Lookup user
            user = get_by_telegram_id(telegram_id)
            if not user:
                json_api_response(self, 404, {"error": "User not found"})
                return

            user_id = user["id"]

            # 2. Gamification stats
            gami_stats = get_user_stats(user_id)

            # 3. Check-in summary tháng
            checkin_stats = _get_checkin_stats_this_month(user_id)

            # 4. Leave balance
            leave_balance = get_remaining_leave_days(user_id)

            json_api_response(self, 200, {
                "ok": True,
                "user": {
                    "id": user["id"],
                    "full_name": user.get("full_name"),
                    "email": user.get("email"),
                    "department": user.get("department"),
                    "role": user.get("role"),
                    "is_active": user.get("is_active"),
                },
                "gamification": gami_stats,
                "checkin_stats": checkin_stats,
                "leave_balance": leave_balance,
            })

        except Exception as e:
            logger.exception("GET /api/me error")
            json_api_response(self, 500, {"ok": False, "error": "Internal error"})

    def do_OPTIONS(self):
        """CORS preflight."""
        handle_cors_preflight(self)
