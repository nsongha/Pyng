"""Vercel Serverless Function — /api/checkins router.

Router cho checkins endpoints:
    - GET /api/checkins             → Paginated check-in history
    - GET /api/checkins/chart       → Chart data cho tháng
    - OPTIONS                       → CORS preflight

Gộp từ checkins.py + checkins/chart.py để giảm function count (Vercel Hobby limit 12).
"""

import logging
from collections import Counter
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from services.auth_service import require_auth, json_api_response, handle_cors_preflight
from services.user_service import get_by_telegram_id
from services.report_service import is_late as check_is_late
from db import client as db
from config.timezone import get_tz
from config.settings import WORK_START

logger = logging.getLogger(__name__)

# --- Constants ---
MAX_LIMIT = 100
DEFAULT_LIMIT = 30
_MIN_YEAR, _MAX_YEAR = 2020, 2100


# ============================================
#  GET /api/checkins — Paginated history
# ============================================

def _get_checkin_history(user_id: int, limit: int, offset: int) -> list[dict]:
    """Lấy lịch sử check-in (đã pair in/out theo ngày).

    Args:
        user_id: ID user.
        limit: Số records trả về.
        offset: Vị trí bắt đầu.

    Returns:
        list[dict]: Danh sách check-in records.
    """
    rows = db.select(
        "checkins",
        columns="id,checked_at,type,method,mood,is_ontime",
        filters={
            "user_id": user_id,
            "type": "in",
        },
        order="checked_at.desc",
        limit=limit,
    )

    if offset > 0:
        all_rows = db.select(
            "checkins",
            columns="id,checked_at,type,method,mood,is_ontime",
            filters={
                "user_id": user_id,
                "type": "in",
            },
            order="checked_at.desc",
            limit=offset + limit,
        )
        rows = all_rows[offset:]

    checkout_rows = db.select(
        "checkins",
        columns="checked_at,type",
        filters={
            "user_id": user_id,
            "type": "out",
        },
        order="checked_at.desc",
    )

    checkout_by_date: dict[str, str] = {}
    for co in checkout_rows:
        co_dt = datetime.fromisoformat(co["checked_at"])
        date_key = co_dt.strftime("%Y-%m-%d")
        if date_key not in checkout_by_date:
            checkout_by_date[date_key] = co["checked_at"]

    result = []
    for row in rows:
        ci_dt = datetime.fromisoformat(row["checked_at"])
        date_key = ci_dt.strftime("%Y-%m-%d")
        time_out = checkout_by_date.get(date_key)

        result.append({
            "date": date_key,
            "time_in": row["checked_at"],
            "time_out": time_out,
            "method": row.get("method"),
            "mood": row.get("mood"),
            "is_ontime": row.get("is_ontime"),
        })

    return result


def _handle_checkins_list(handler_self) -> None:
    """GET /api/checkins — Paginated check-in history."""
    try:
        telegram_id = handler_self._telegram_user["id"]

        user = get_by_telegram_id(telegram_id)
        if not user:
            json_api_response(handler_self, 404, {"error": "User not found"})
            return

        parsed_url = urlparse(handler_self.path)
        params = parse_qs(parsed_url.query)
        limit = min(int(params.get("limit", [DEFAULT_LIMIT])[0]), MAX_LIMIT)
        offset = max(int(params.get("offset", [0])[0]), 0)

        records = _get_checkin_history(user["id"], limit, offset)

        json_api_response(handler_self, 200, {
            "ok": True,
            "data": records,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "count": len(records),
            },
        })

    except Exception:
        logger.exception("GET /api/checkins error")
        json_api_response(handler_self, 500, {"ok": False, "error": "Internal error"})


# ============================================
#  GET /api/checkins/chart — Chart data
# ============================================

def _get_chart_data(user_id: int, month: int, year: int) -> dict:
    """Tính chart data cho 1 user trong 1 tháng.

    Args:
        user_id: ID user.
        month: Tháng (1-12).
        year: Năm.

    Returns:
        dict: {daily_hours, summary, trend}
    """
    tz = get_tz()

    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    start_iso = datetime(
        first_day.year, first_day.month, first_day.day,
        0, 0, 0, tzinfo=tz,
    ).isoformat()
    end_iso = datetime(
        last_day.year, last_day.month, last_day.day,
        23, 59, 59, tzinfo=tz,
    ).isoformat()

    checkins = db.select(
        "checkins",
        columns="id,checked_at,method,mood,is_ontime",
        filters={
            "user_id": user_id,
            "type": "in",
            "checked_at.gte": start_iso,
            "checked_at.lt": end_iso,
        },
        order="checked_at.asc",
    )

    checkouts = db.select(
        "checkins",
        columns="id,checked_at,user_id",
        filters={
            "user_id": user_id,
            "type": "out",
            "checked_at.gte": start_iso,
            "checked_at.lt": end_iso,
        },
        order="checked_at.asc",
    )

    checkout_by_date: dict[str, str] = {}
    for co in checkouts:
        co_dt = datetime.fromisoformat(co["checked_at"])
        date_key = co_dt.strftime("%Y-%m-%d")
        if date_key not in checkout_by_date:
            checkout_by_date[date_key] = co["checked_at"]

    checkin_by_date: dict[str, dict] = {}
    for ci in checkins:
        ci_dt = datetime.fromisoformat(ci["checked_at"])
        date_key = ci_dt.strftime("%Y-%m-%d")
        if date_key not in checkin_by_date:
            checkin_by_date[date_key] = ci

    daily_hours = []
    total_hours = 0.0
    ontime_count = 0
    methods_counter: Counter = Counter()

    num_days = last_day.day
    for day_num in range(1, num_days + 1):
        current_date = date(year, month, day_num)
        date_key = current_date.isoformat()

        ci = checkin_by_date.get(date_key)
        if ci is None:
            daily_hours.append({
                "date": date_key,
                "hours": 0,
                "is_late": False,
                "method": None,
                "mood": None,
            })
            continue

        co_str = checkout_by_date.get(date_key)
        hours = 0.0
        if co_str:
            ci_dt = datetime.fromisoformat(ci["checked_at"])
            co_dt = datetime.fromisoformat(co_str)
            diff = co_dt - ci_dt
            hours = round(diff.total_seconds() / 3600, 1)
            hours = max(0, hours)

        is_late = check_is_late(ci["checked_at"])
        method = ci.get("method")
        mood = ci.get("mood")

        if not is_late:
            ontime_count += 1
        if method:
            methods_counter[method] += 1
        total_hours += hours

        daily_hours.append({
            "date": date_key,
            "hours": hours,
            "is_late": is_late,
            "method": method,
            "mood": mood,
        })

    total_days = len(checkin_by_date)
    avg_hours = round(total_hours / total_days, 1) if total_days > 0 else 0
    ontime_rate = round(ontime_count / total_days * 100, 1) if total_days > 0 else 0
    most_used_method = methods_counter.most_common(1)[0][0] if methods_counter else None

    summary = {
        "avg_hours": avg_hours,
        "total_days": total_days,
        "ontime_rate": ontime_rate,
        "most_used_method": most_used_method,
    }

    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    prev_avg = _get_month_avg_hours(user_id, prev_month, prev_year)

    change_percent = 0.0
    if prev_avg > 0:
        change_percent = round((avg_hours - prev_avg) / prev_avg * 100, 1)

    trend = {
        "prev_month_avg": prev_avg,
        "current_avg": avg_hours,
        "change_percent": change_percent,
    }

    return {
        "daily_hours": daily_hours,
        "summary": summary,
        "trend": trend,
    }


def _get_month_avg_hours(user_id: int, month: int, year: int) -> float:
    """Tính trung bình giờ làm của tháng trước (lightweight)."""
    tz = get_tz()
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    start_iso = datetime(
        first_day.year, first_day.month, first_day.day,
        0, 0, 0, tzinfo=tz,
    ).isoformat()
    end_iso = datetime(
        last_day.year, last_day.month, last_day.day,
        23, 59, 59, tzinfo=tz,
    ).isoformat()

    checkins = db.select(
        "checkins",
        columns="checked_at",
        filters={
            "user_id": user_id,
            "type": "in",
            "checked_at.gte": start_iso,
            "checked_at.lt": end_iso,
        },
        order="checked_at.asc",
    )

    checkouts = db.select(
        "checkins",
        columns="checked_at",
        filters={
            "user_id": user_id,
            "type": "out",
            "checked_at.gte": start_iso,
            "checked_at.lt": end_iso,
        },
        order="checked_at.asc",
    )

    checkout_by_date: dict[str, str] = {}
    for co in checkouts:
        co_dt = datetime.fromisoformat(co["checked_at"])
        dk = co_dt.strftime("%Y-%m-%d")
        if dk not in checkout_by_date:
            checkout_by_date[dk] = co["checked_at"]

    total_hours = 0.0
    days_counted = 0
    seen_dates: set[str] = set()

    for ci in checkins:
        ci_dt = datetime.fromisoformat(ci["checked_at"])
        dk = ci_dt.strftime("%Y-%m-%d")
        if dk in seen_dates:
            continue
        seen_dates.add(dk)

        co_str = checkout_by_date.get(dk)
        if co_str:
            co_dt = datetime.fromisoformat(co_str)
            hours = (co_dt - ci_dt).total_seconds() / 3600
            total_hours += max(0, hours)
            days_counted += 1

    return round(total_hours / days_counted, 1) if days_counted > 0 else 0.0


def _handle_chart_data(handler_self) -> None:
    """GET /api/checkins/chart — Chart data cho tháng."""
    try:
        telegram_id = handler_self._telegram_user["id"]

        user = get_by_telegram_id(telegram_id)
        if not user:
            json_api_response(handler_self, 404, {"error": "User not found"})
            return

        parsed_url = urlparse(handler_self.path)
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
                json_api_response(handler_self, 400, {"error": "Invalid month format. Use YYYY-MM"})
                return
        else:
            year = now.year
            month = now.month

        if month < 1 or month > 12 or year < _MIN_YEAR or year > _MAX_YEAR:
            json_api_response(handler_self, 400, {"error": "Invalid month/year"})
            return

        chart_data = _get_chart_data(user["id"], month, year)

        json_api_response(handler_self, 200, {
            "ok": True,
            "month": f"{year}-{month:02d}",
            **chart_data,
        })

    except Exception:
        logger.exception("GET /api/checkins/chart error")
        json_api_response(handler_self, 500, {"ok": False, "error": "Internal error"})


# --- Vercel Handler ---

class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler — /api/checkins router.

    Routes:
        GET /api/checkins        → _handle_checkins_list
        GET /api/checkins/chart  → _handle_chart_data
    """

    @require_auth
    def do_GET(self):
        """Route GET requests by path."""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path.endswith("/checkins/chart"):
            _handle_chart_data(self)
        else:
            # Default: /api/checkins (list)
            _handle_checkins_list(self)

    def do_OPTIONS(self):
        """CORS preflight."""
        handle_cors_preflight(self)
