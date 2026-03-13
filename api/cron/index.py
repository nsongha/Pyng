"""Vercel Serverless Function — Cron Dispatcher.

Endpoint: POST /api/cron?task=<task_name>
Gộp tất cả cron tasks vào 1 serverless function để tiết kiệm Vercel Hobby limit (12 functions).

Supported tasks:
  - morning      — Nhắc check-in buổi sáng (8:30 AM, weekday)
  - evening      — Nhắc check-out buổi chiều (17:45 PM, weekday)
  - daily_report — Báo cáo hàng ngày vào admin group (9:15 AM, weekday)
  - qr_refresh   — Refresh QR code (mỗi 5 phút, giờ làm việc)
  - weekly       — Leaderboard + streak reminder (Monday 9:00 AM)
"""

import asyncio
import logging
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

from services.cron_helpers import verify_cron_secret, json_response


# ------------------------------------------------------------------
# Task: morning — Nhắc check-in
# ------------------------------------------------------------------

async def _run_morning() -> dict:
    from services.user_service import get_all_active_users
    from services.checkin_service import has_checked_in_today
    from services.cron_helpers import send_telegram_message

    users = get_all_active_users()
    sent = 0
    skipped = 0
    errors = []

    for user in users:
        user_id = user.get("id")
        telegram_id = user.get("telegram_id")
        full_name = user.get("full_name", "bạn")

        if not telegram_id:
            continue

        if has_checked_in_today(user_id):
            skipped += 1
            continue

        try:
            text = (
                f"🌅 Chào buổi sáng, *{full_name}*!\n"
                f"Hôm nay bạn làm việc ở đâu?\n"
            )
            reply_markup = {
                "inline_keyboard": [[
                    {"text": "🏢 Tại văn phòng", "callback_data": "checkin_office"},
                    {"text": "🏠 WFH hôm nay", "callback_data": "checkin_wfh"},
                ]]
            }
            await send_telegram_message(
                chat_id=telegram_id, text=text, reply_markup=reply_markup,
            )
            sent += 1
        except Exception as e:
            errors.append({"user_id": user_id, "error": str(e)})

    return {"total_active": len(users), "sent": sent, "skipped_already_checked_in": skipped, "errors": errors}


# ------------------------------------------------------------------
# Task: evening — Nhắc check-out
# ------------------------------------------------------------------

async def _run_evening() -> dict:
    from services.user_service import get_all_active_users
    from services.checkin_service import has_checked_in_today, get_today_checkin
    from services.cron_helpers import send_telegram_message

    users = get_all_active_users()
    sent = 0
    skipped = 0
    errors = []

    for user in users:
        user_id = user.get("id")
        telegram_id = user.get("telegram_id")
        full_name = user.get("full_name", "bạn")

        if not telegram_id:
            continue

        if not has_checked_in_today(user_id):
            skipped += 1
            continue

        checkout = get_today_checkin(user_id, "out")
        if checkout is not None:
            skipped += 1
            continue

        try:
            text = f"🌆 Hết giờ rồi, *{full_name}*!\nĐừng quên check-out nhé."
            reply_markup = {"inline_keyboard": [[{"text": "🚪 CHECK OUT", "callback_data": "checkout"}]]}
            await send_telegram_message(
                chat_id=telegram_id, text=text, reply_markup=reply_markup,
            )
            sent += 1
        except Exception as e:
            errors.append({"user_id": user_id, "error": str(e)})

    return {"total_active": len(users), "sent": sent, "skipped_no_checkin_or_already_out": skipped, "errors": errors}


# ------------------------------------------------------------------
# Task: daily_report — Báo cáo hàng ngày
# ------------------------------------------------------------------

async def _run_daily_report() -> dict:
    from services.report_service import generate_daily_text_report
    from services.cron_helpers import send_telegram_message
    from config.settings import ADMIN_GROUP_ID

    if not ADMIN_GROUP_ID:
        return {"ok": False, "error": "ADMIN_GROUP_ID not configured"}

    report_text = generate_daily_text_report()
    result = await send_telegram_message(chat_id=ADMIN_GROUP_ID, text=report_text)
    return {"ok": True, "chat_id": ADMIN_GROUP_ID, "telegram_response": result}


# ------------------------------------------------------------------
# Task: qr_refresh — Refresh QR code
# ------------------------------------------------------------------

def _run_qr_refresh() -> dict:
    from services.qr_service import cleanup_expired_qr, get_current_qr
    from services.office_service import get_active_office
    from config.timezone import get_tz
    from config.settings import WORK_START, WORK_END

    # Kiểm tra giờ làm việc
    tz = get_tz()
    now = datetime.now(tz)
    if now.weekday() >= 5:
        return {"ok": True, "action": "skipped", "reason": "Ngoài giờ làm việc (weekend)"}

    start_h, start_m = map(int, WORK_START.split(":"))
    end_h, end_m = map(int, WORK_END.split(":"))
    start_minutes = start_h * 60 + start_m
    end_minutes = end_h * 60 + end_m
    current_minutes = now.hour * 60 + now.minute
    if not ((start_minutes - 30) <= current_minutes <= (end_minutes + 30)):
        return {"ok": True, "action": "skipped", "reason": "Ngoài giờ làm việc"}

    deleted = cleanup_expired_qr()

    office = get_active_office()
    if not office:
        return {"ok": True, "action": "skipped", "reason": "Không có office active"}

    qr_session = get_current_qr(office["id"])
    return {
        "ok": True,
        "action": "refreshed",
        "expired_cleaned": len(deleted) if isinstance(deleted, list) else 0,
        "current_token": qr_session["token"],
        "expire_at": qr_session["expire_at"],
    }


# ------------------------------------------------------------------
# Task: weekly — Leaderboard + Streak reminder
# ------------------------------------------------------------------

async def _run_weekly() -> dict:
    from services.gamification_service import get_leaderboard
    from services.user_service import get_all_active_users
    from services.cron_helpers import send_telegram_message
    from config.settings import ADMIN_GROUP_ID
    from config.timezone import get_tz
    from db import client as db

    # --- Leaderboard → Admin Group ---
    lb_result = {"ok": False, "error": "skipped"}

    if ADMIN_GROUP_ID:
        board = get_leaderboard(period="month", limit=10)
        if board:
            user_ids = [entry["user_id"] for entry in board]
            all_users = db.select("users", columns="id,full_name")
            id_set = set(user_ids)
            user_names = {
                u["id"]: u.get("full_name", f"User #{u['id']}")
                for u in all_users if u["id"] in id_set
            }

            now = datetime.now(get_tz())
            week_num = now.isocalendar()[1]
            rank_icons = {1: "🥇", 2: "🥈", 3: "🥉"}

            lines = [f"🏆 LEADERBOARD TUẦN #{week_num}", "━━━━━━━━━━━━━━━━━━━━"]
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

            result = await send_telegram_message(chat_id=ADMIN_GROUP_ID, text="\n".join(lines))
            lb_result = {"ok": True, "leaderboard": "sent", "entries": len(board), "telegram": result}
        else:
            lb_result = {"ok": True, "leaderboard": "empty", "sent": False}

    # --- Streak Reminder → DM ---
    active_users = get_all_active_users()
    all_gami = db.select("gamification", columns="user_id,current_streak")
    gami_map = {g["user_id"]: g["current_streak"] for g in all_gami}

    sr_sent = 0
    sr_errors = 0

    for u in active_users:
        uid = u["id"]
        streak = gami_map.get(uid, 0)
        if streak <= 0:
            continue

        telegram_id = u.get("telegram_id")
        if not telegram_id:
            continue

        name = u.get("full_name", "Bạn")
        if streak >= 30: icon = "💎"
        elif streak >= 20: icon = "⚡"
        elif streak >= 10: icon = "🔥🔥🔥"
        elif streak >= 5: icon = "🔥🔥"
        else: icon = "🔥"

        text = (
            f"Chào {name}! {icon}\n\n"
            f"Streak hiện tại: *{streak} ngày* liên tiếp!\n"
            f"Đừng quên check-in tuần này để giữ streak nhé 💪\n\n"
            f"Gõ /points để xem thống kê chi tiết."
        )
        try:
            await send_telegram_message(chat_id=telegram_id, text=text)
            sr_sent += 1
        except Exception:
            logger.error("Failed to send streak reminder to user %s", uid)
            sr_errors += 1
        await asyncio.sleep(0.05)

    return {
        "type": "weekly",
        "leaderboard": lb_result,
        "streak_reminders": {"ok": True, "reminders_sent": sr_sent, "errors": sr_errors},
    }


# ------------------------------------------------------------------
# Task Registry
# ------------------------------------------------------------------

TASK_REGISTRY = {
    "morning": _run_morning,
    "evening": _run_evening,
    "daily_report": _run_daily_report,
    "qr_refresh": _run_qr_refresh,  # sync function
    "weekly": _run_weekly,
}


# ------------------------------------------------------------------
# Vercel Serverless Handler
# ------------------------------------------------------------------

class handler(BaseHTTPRequestHandler):
    """Cron dispatcher — gộp tất cả cron tasks vào 1 function."""

    def do_POST(self):
        # 1. Verify CRON_SECRET
        auth = self.headers.get("Authorization")
        if not verify_cron_secret(auth):
            json_response(self, 401, {"error": "Unauthorized"})
            return

        # 2. Xác định task từ query param
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        task_name = params.get("task", [None])[0]

        if not task_name or task_name not in TASK_REGISTRY:
            json_response(self, 400, {
                "error": f"Invalid task: {task_name}",
                "available_tasks": list(TASK_REGISTRY.keys()),
            })
            return

        # 3. Chạy task
        try:
            task_fn = TASK_REGISTRY[task_name]
            if asyncio.iscoroutinefunction(task_fn):
                result = asyncio.run(task_fn())
            else:
                result = task_fn()

            json_response(self, 200, {"ok": True, "type": task_name, **result})
        except Exception as e:
            logger.exception("Cron task '%s' error", task_name)
            json_response(self, 500, {"ok": False, "error": "Internal error"})

    def do_GET(self):
        """Health check — liệt kê available tasks."""
        json_response(self, 200, {
            "status": "ok",
            "endpoint": "cron-dispatcher",
            "available_tasks": list(TASK_REGISTRY.keys()),
            "usage": "POST /api/cron?task=<task_name>",
        })
