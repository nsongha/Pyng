"""Vercel Serverless Function — Weekly Leaderboard & Streak Reminder.

Endpoint: POST /api/cron/weekly
Trigger: GitHub Actions cron — Monday 9:00 AM (UTC+7) = 02:00 UTC.

1. Gửi leaderboard tuần trước vào admin group.
2. Gửi streak reminder cá nhân cho users có streak > 0.
"""

import asyncio
import logging
from http.server import BaseHTTPRequestHandler

logger = logging.getLogger(__name__)

from services.gamification_service import get_leaderboard
from services.user_service import get_all_active_users
from services.cron_helpers import verify_cron_secret, send_telegram_message, json_response
from config.settings import ADMIN_GROUP_ID
from db import client as db


# ------------------------------------------------------------------
# Weekly Leaderboard → Admin Group
# ------------------------------------------------------------------

def _get_user_names(user_ids: list[int]) -> dict[int, str]:
    """Batch lấy full_name cho list user IDs."""
    if not user_ids:
        return {}
    all_users = db.select("users", columns="id,full_name")
    id_set = set(user_ids)
    return {
        u["id"]: u.get("full_name", f"User #{u['id']}")
        for u in all_users
        if u["id"] in id_set
    }


async def _send_weekly_leaderboard() -> dict:
    """Tạo và gửi weekly leaderboard vào admin group.

    Returns:
        dict: Summary kết quả gửi.
    """
    if not ADMIN_GROUP_ID:
        return {"ok": False, "error": "ADMIN_GROUP_ID not configured"}

    board = get_leaderboard(period="month", limit=10)

    if not board:
        return {"ok": True, "leaderboard": "empty", "sent": False}

    # Lấy tên users
    user_ids = [entry["user_id"] for entry in board]
    user_names = _get_user_names(user_ids)

    # Format message
    from datetime import datetime
    from config.timezone import get_tz

    now = datetime.now(get_tz())
    week_num = now.isocalendar()[1]
    rank_icons = {1: "🥇", 2: "🥈", 3: "🥉"}

    lines = [
        f"🏆 LEADERBOARD TUẦN #{week_num}",
        "━━━━━━━━━━━━━━━━━━━━",
    ]

    for entry in board:
        rank = entry["rank"]
        uid = entry["user_id"]
        pts = entry.get("month_points", entry.get("total_points", 0))
        streak = entry.get("current_streak", 0)
        name = user_names.get(uid, f"User #{uid}")

        icon = rank_icons.get(rank, f"{rank}.")
        streak_str = f" 🔥{streak}" if streak > 0 else ""
        lines.append(f"{icon} {name} — {pts} pts{streak_str}")

    lines.append("━━━━━━━━━━━━━━━━━━━━")
    lines.append("💡 Gõ /leaderboard để xem chi tiết.")

    text = "\n".join(lines)

    result = await send_telegram_message(
        chat_id=ADMIN_GROUP_ID,
        text=text,
    )

    return {"ok": True, "leaderboard": "sent", "entries": len(board), "telegram": result}


# ------------------------------------------------------------------
# Streak Reminder → DM cho users có streak > 0
# ------------------------------------------------------------------

async def _send_streak_reminders() -> dict:
    """Gửi streak reminder cá nhân cho active users có streak > 0.

    Returns:
        dict: Summary kết quả gửi.
    """
    active_users = get_all_active_users()
    if not active_users:
        return {"ok": True, "reminders_sent": 0}

    # Lấy gamification data cho tất cả users
    user_ids = [u["id"] for u in active_users]
    all_gami = db.select("gamification", columns="user_id,current_streak")
    gami_map = {g["user_id"]: g["current_streak"] for g in all_gami}

    # Build telegram_id map
    tid_map = {u["id"]: u["telegram_id"] for u in active_users}
    name_map = {u["id"]: u.get("full_name", "Bạn") for u in active_users}

    sent = 0
    errors = 0

    for uid in user_ids:
        streak = gami_map.get(uid, 0)
        if streak <= 0:
            continue

        telegram_id = tid_map.get(uid)
        if not telegram_id:
            continue

        name = name_map.get(uid, "Bạn")

        # Streak level icons
        if streak >= 30:
            icon = "💎"
        elif streak >= 20:
            icon = "⚡"
        elif streak >= 10:
            icon = "🔥🔥🔥"
        elif streak >= 5:
            icon = "🔥🔥"
        else:
            icon = "🔥"

        text = (
            f"Chào {name}! {icon}\n\n"
            f"Streak hiện tại: *{streak} ngày* liên tiếp!\n"
            f"Đừng quên check-in tuần này để giữ streak nhé 💪\n\n"
            f"Gõ /points để xem thống kê chi tiết."
        )

        try:
            await send_telegram_message(chat_id=telegram_id, text=text)
            sent += 1
        except Exception:
            logger.error("Failed to send streak reminder to user %s", uid)
            errors += 1

        # Rate limit — tránh Telegram 30 msg/s
        await asyncio.sleep(0.05)

    return {"ok": True, "reminders_sent": sent, "errors": errors}


# ------------------------------------------------------------------
# Vercel Serverless Handler
# ------------------------------------------------------------------

class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler — Weekly leaderboard + streak reminder."""

    def do_POST(self):
        """Xử lý POST request từ GitHub Actions cron (Monday 9:00 AM)."""
        # 1. Verify CRON_SECRET
        auth = self.headers.get("Authorization")
        if not verify_cron_secret(auth):
            json_response(self, 401, {"error": "Unauthorized"})
            return

        try:
            # 2. Gửi leaderboard vào admin group
            lb_result = asyncio.run(_send_weekly_leaderboard())

            # 3. Gửi streak reminders cho cá nhân
            sr_result = asyncio.run(_send_streak_reminders())

            json_response(self, 200, {
                "type": "weekly",
                "leaderboard": lb_result,
                "streak_reminders": sr_result,
            })
        except Exception as e:
            logger.exception("Cron weekly error")
            json_response(self, 500, {"ok": False, "error": "Internal error"})

    def do_GET(self):
        """Health check."""
        json_response(self, 200, {
            "status": "ok",
            "endpoint": "weekly",
            "message": "Send POST with Authorization header to trigger.",
        })
