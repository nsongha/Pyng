"""Vercel Serverless Function — GET /api/leaderboard.

Endpoint: GET /api/leaderboard?period=month
Auth: Telegram initData (X-Telegram-Init-Data header)

Trả về top 10 users + vị trí user hiện tại.
Period: 'month' (default) | 'alltime'.
"""

import logging
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from services.auth_service import require_auth, json_api_response, handle_cors_preflight
from services.user_service import get_by_telegram_id
from services.gamification_service import get_leaderboard, get_user_stats
from db import client as db

logger = logging.getLogger(__name__)


def _enrich_leaderboard_with_names(leaderboard: list[dict]) -> list[dict]:
    """Thêm tên users vào leaderboard entries.

    Args:
        leaderboard: Danh sách từ get_leaderboard().

    Returns:
        list[dict]: Leaderboard entries có thêm full_name.
    """
    if not leaderboard:
        return leaderboard

    # Batch query tất cả user names (1 query thay vì N — fix TD-001)
    user_ids = [entry["user_id"] for entry in leaderboard]
    all_users = db.select("users", columns="id,full_name")
    id_set = set(user_ids)
    name_map = {
        u["id"]: u.get("full_name", "Unknown")
        for u in all_users
        if u["id"] in id_set
    }

    for entry in leaderboard:
        entry["full_name"] = name_map.get(entry["user_id"], "Unknown")

    return leaderboard


class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler — GET /api/leaderboard."""

    @require_auth
    def do_GET(self):
        """Trả về leaderboard + user rank."""
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
            period = params.get("period", ["month"])[0]

            # Validate period
            if period not in ("month", "alltime"):
                period = "month"

            # Lấy leaderboard
            top_users = get_leaderboard(period=period, limit=10)
            top_users = _enrich_leaderboard_with_names(top_users)

            # Lấy user stats (bao gồm rank)
            user_stats = get_user_stats(user["id"])

            json_api_response(self, 200, {
                "ok": True,
                "period": period,
                "leaderboard": top_users,
                "user_rank": {
                    "rank": user_stats.get("rank"),
                    "total_points": user_stats.get("total_points"),
                    "current_streak": user_stats.get("current_streak"),
                    "full_name": user.get("full_name"),
                },
            })

        except Exception as e:
            logger.exception("GET /api/leaderboard error")
            json_api_response(self, 500, {"ok": False, "error": "Internal error"})

    def do_OPTIONS(self):
        """CORS preflight."""
        handle_cors_preflight(self)
