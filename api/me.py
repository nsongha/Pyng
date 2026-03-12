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

    Returns dict khớp với TypeScript CheckinStats interface:
        {total_days, late_days, wfh_days, leave_days, ontime_percentage}

    Note: Column `is_ontime` KHÔNG tồn tại trong DB checkins table.
    Ontime được tính từ `checked_at` timestamp, giống report_service.is_late().

    Args:
        user_id: ID user (bảng users.id).

    Returns:
        dict: CheckinStats-compatible format.
    """
    from services.report_service import is_late as check_is_late

    tz = get_tz()
    now = datetime.now(tz)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if now.month == 12:
        end = start.replace(year=now.year + 1, month=1)
    else:
        end = start.replace(month=now.month + 1)

    # Note: KHÔNG query is_ontime vì column này không tồn tại trong DB
    rows = db.select(
        "checkins",
        columns="id,method,checked_at,type",
        filters={
            "user_id": user_id,
            "type": "in",
            "checked_at.gte": start.isoformat(),
            "checked_at.lt": end.isoformat(),
        },
    )

    total_days = len(rows)
    wfh_days = sum(1 for r in rows if r.get("method") == "wfh")

    # Tính late từ checked_at (giống report_service.is_late)
    late_days = 0
    for r in rows:
        if r.get("method") == "wfh":
            continue  # WFH không tính muộn
        checked_at = r.get("checked_at")
        if checked_at and check_is_late(checked_at):
            late_days += 1

    ontime = max(0, total_days - late_days - wfh_days)

    # Leave days tháng này (approved)
    leave_rows = db.select(
        "leaves",
        columns="days_count",
        filters={
            "user_id": user_id,
            "status": "approved",
            "start_date.gte": start.strftime("%Y-%m-%d"),
            "start_date.lt": end.strftime("%Y-%m-%d"),
        },
    )
    leave_days = sum(float(r.get("days_count", 0)) for r in leave_rows)

    ontime_percentage = round(ontime / total_days * 100, 1) if total_days > 0 else 0

    return {
        "total_days": total_days,
        "late_days": late_days,
        "wfh_days": wfh_days,
        "leave_days": leave_days,
        "ontime_percentage": ontime_percentage,
    }


class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler — GET /api/me."""

    def do_GET(self):
        """Route: debug mode hoặc normal auth flow."""
        from urllib.parse import urlparse, parse_qs as _parse_qs
        parsed = urlparse(self.path)
        qs = _parse_qs(parsed.query)

        if qs.get("debug"):
            return self._handle_debug()

        if qs.get("auth_debug"):
            return self._handle_auth_debug()

        return self._handle_me()

    @require_auth
    def _handle_me(self):
        """Trả về user dashboard data."""

        telegram_id = None
        try:
            telegram_id = self._telegram_user["id"]

            # 1. Lookup user
            user = get_by_telegram_id(telegram_id)
            if not user:
                json_api_response(self, 404, {"ok": False, "error": "User not found"})
                return

            user_id = user["id"]

            # 2. Gamification stats (safe — user chưa có record thì trả default)
            try:
                gami_stats = get_user_stats(user_id)
            except Exception:
                logger.warning("get_user_stats failed for user_id=%s", user_id)
                gami_stats = {
                    "total_points": 0,
                    "current_streak": 0,
                    "longest_streak": 0,
                    "rank": 0,
                    "ontime_count": 0,
                    "early_count": 0,
                    "streak_label": "🔥 Đang khởi động",
                }

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
            logger.exception("GET /api/me error — telegram_id=%s", telegram_id)
            json_api_response(self, 500, {"ok": False, "error": f"Internal error: {type(e).__name__}"})

    def _handle_debug(self):
        """Debug endpoint tạm thời — test DB calls."""
        import traceback
        results = {}

        try:
            # Test 1: Users
            try:
                users = db.select("users", columns="id,telegram_id,full_name", limit=1)
                results["users"] = {"ok": True, "count": len(users), "sample": users[:1]}
            except Exception as e:
                results["users"] = {"ok": False, "error": f"{type(e).__name__}: {e}"}

            # Test 2: Checkins (without is_ontime!)
            try:
                tz = get_tz()
                now = datetime.now(tz)
                start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                checkins = db.select(
                    "checkins", columns="id,method,checked_at,type",
                    filters={"type": "in", "checked_at.gte": start.isoformat()},
                    limit=2,
                )
                results["checkins"] = {"ok": True, "count": len(checkins)}
            except Exception as e:
                results["checkins"] = {"ok": False, "error": f"{type(e).__name__}: {e}", "tb": traceback.format_exc()[-300:]}

            # Test 3: Leaves
            try:
                leaves = db.select("leaves", columns="id,user_id,days_count,status", limit=2)
                results["leaves"] = {"ok": True, "count": len(leaves)}
            except Exception as e:
                results["leaves"] = {"ok": False, "error": f"{type(e).__name__}: {e}"}

            # Test 4: Gamification
            try:
                gami = db.select("gamification", columns="id,user_id,total_points", limit=2)
                results["gamification"] = {"ok": True, "count": len(gami)}
            except Exception as e:
                results["gamification"] = {"ok": False, "error": f"{type(e).__name__}: {e}"}

            # Test 5: Full /api/me flow for first user
            if results.get("users", {}).get("ok") and results["users"]["sample"]:
                uid = results["users"]["sample"][0]["id"]
                try:
                    stats = _get_checkin_stats_this_month(uid)
                    results["checkin_stats"] = {"ok": True, "data": stats}
                except Exception as e:
                    results["checkin_stats"] = {"ok": False, "error": f"{type(e).__name__}: {e}", "tb": traceback.format_exc()[-300:]}
                try:
                    balance = get_remaining_leave_days(uid)
                    results["leave_balance"] = {"ok": True, "data": balance}
                except Exception as e:
                    results["leave_balance"] = {"ok": False, "error": f"{type(e).__name__}: {e}"}
                try:
                    gstats = get_user_stats(uid)
                    results["user_stats"] = {"ok": True, "data": gstats}
                except Exception as e:
                    results["user_stats"] = {"ok": False, "error": f"{type(e).__name__}: {e}", "tb": traceback.format_exc()[-300:]}

        except Exception as e:
            results["init"] = {"ok": False, "error": f"{type(e).__name__}: {e}"}

        import json as _json
        body = _json.dumps(results, default=str, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        """CORS preflight."""
        handle_cors_preflight(self)
