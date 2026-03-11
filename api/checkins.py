"""Vercel Serverless Function — GET /api/checkins.

Endpoint: GET /api/checkins?limit=30&offset=0
Auth: Telegram initData (X-Telegram-Init-Data header)

Trả về paginated check-in history cho user.
Mỗi record: date, time_in, time_out, method, mood, is_ontime.
"""

import logging
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from services.auth_service import require_auth, json_api_response, handle_cors_preflight
from services.user_service import get_by_telegram_id
from db import client as db

logger = logging.getLogger(__name__)

# Giới hạn tối đa 1 lần query
MAX_LIMIT = 100
DEFAULT_LIMIT = 30


def _get_checkin_history(user_id: int, limit: int, offset: int) -> list[dict]:
    """Lấy lịch sử check-in (đã pair in/out theo ngày).

    Args:
        user_id: ID user.
        limit: Số records trả về.
        offset: Vị trí bắt đầu.

    Returns:
        list[dict]: Danh sách check-in records.
    """
    # Lấy check-in records (type='in'), mới nhất trước
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

    # Nếu có offset, cần skip
    # PostgREST hỗ trợ offset qua Range header, nhưng db client chưa có
    # → lấy nhiều hơn rồi slice (chấp nhận cho < 50 users)
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

    # Lấy tất cả checkout records để pair
    checkout_rows = db.select(
        "checkins",
        columns="checked_at,type",
        filters={
            "user_id": user_id,
            "type": "out",
        },
        order="checked_at.desc",
    )

    # Index checkout theo ngày
    checkout_by_date: dict[str, str] = {}
    for co in checkout_rows:
        co_dt = datetime.fromisoformat(co["checked_at"])
        date_key = co_dt.strftime("%Y-%m-%d")
        if date_key not in checkout_by_date:
            checkout_by_date[date_key] = co["checked_at"]

    # Build result
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


class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler — GET /api/checkins."""

    @require_auth
    def do_GET(self):
        """Trả về paginated check-in history."""
        try:
            telegram_id = self._telegram_user["id"]

            # Lookup user
            user = get_by_telegram_id(telegram_id)
            if not user:
                json_api_response(self, 404, {"error": "User not found"})
                return

            # Parse query params
            parsed_url = urlparse(self.path)
            params = parse_qs(parsed_url.query)
            limit = min(int(params.get("limit", [DEFAULT_LIMIT])[0]), MAX_LIMIT)
            offset = max(int(params.get("offset", [0])[0]), 0)

            # Lấy history
            records = _get_checkin_history(user["id"], limit, offset)

            json_api_response(self, 200, {
                "ok": True,
                "data": records,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "count": len(records),
                },
            })

        except Exception as e:
            logger.exception("GET /api/checkins error")
            json_api_response(self, 500, {"ok": False, "error": "Internal error"})

    def do_OPTIONS(self):
        """CORS preflight."""
        handle_cors_preflight(self)
