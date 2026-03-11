"""Pyng — Gamification Handlers.

B2: Leaderboard command (/leaderboard, /xh) — top 10 tháng.
B3: Stats/Points command (/points, /diem) — thống kê cá nhân.
B4: Streak display helper — dòng gamification cho check-in response.
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from services.gamification_service import get_leaderboard, get_user_stats
from services.checkin_service import process_gamification_after_checkin
from bot.handlers._helpers import get_active_user_or_none
from db import client as db

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# B2: Leaderboard Command
# ------------------------------------------------------------------


async def leaderboard_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Lệnh /leaderboard hoặc /xh — top 10 điểm tháng này.

    Format theo GAMIFICATION_DESIGN.md §5.1.
    Hiển thị vị trí user nếu không trong top 10.
    """
    user = get_active_user_or_none(update.effective_user.id)
    if not user:
        await update.message.reply_text(
            "❌ Bạn chưa đăng ký hoặc chưa được duyệt.\nGõ /start để đăng ký."
        )
        return

    # Lấy leaderboard tháng
    board = get_leaderboard(period="month", limit=10)

    if not board:
        await update.message.reply_text(
            "📊 Chưa có dữ liệu điểm tháng này.\n"
            "Hãy check-in để bắt đầu tích điểm! 🎯"
        )
        return

    # Lấy tên users (batch query tránh N+1)
    user_ids = [entry["user_id"] for entry in board]
    user_names = _get_user_names_by_ids(user_ids)

    # Header
    from datetime import datetime
    from config.timezone import get_tz

    now = datetime.now(get_tz())
    month_year = now.strftime("%m/%Y")
    lines = [
        f"🏆 BẢNG XẾP HẠNG — Tháng {month_year}",
        "━━━━━━━━━━━━━━━━━━━━",
    ]

    # Rank icons
    rank_icons = {1: "🥇", 2: "🥈", 3: "🥉"}

    for entry in board:
        rank = entry["rank"]
        uid = entry["user_id"]
        pts = entry.get("month_points", entry.get("total_points", 0))
        streak = entry.get("current_streak", 0)
        name = user_names.get(uid, f"User #{uid}")

        icon = rank_icons.get(rank, f"{rank}.")
        streak_str = f" 🔥 {streak}" if streak > 0 else ""
        lines.append(f"{icon} {name}    — {pts} pts{streak_str}")

    lines.append("━━━━━━━━━━━━━━━━━━━━")

    # Hiển thị vị trí user nếu không trong top 10
    user_in_top = any(e["user_id"] == user["id"] for e in board)
    if not user_in_top:
        stats = get_user_stats(user["id"])
        rank = stats.get("rank", "?")
        total_pts = stats.get("total_points", 0)
        streak = stats.get("current_streak", 0)
        streak_str = f" 🔥 {streak}" if streak > 0 else ""
        lines.append(f"Bạn đang ở vị trí #{rank} — {total_pts} pts{streak_str}")

        # Tính khoảng cách tới top 10
        if board:
            last_top = board[-1].get("month_points", board[-1].get("total_points", 0))
            gap = last_top - total_pts
            if gap > 0:
                lines.append(f"Cách top 10: {gap} điểm 👆 Come on!")
    else:
        lines.append("✨ Bạn đang trong TOP 10! Keep going!")

    await update.message.reply_text("\n".join(lines))


# ------------------------------------------------------------------
# B3: Stats / Points Command
# ------------------------------------------------------------------


async def points_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Lệnh /points hoặc /diem — thống kê gamification cá nhân.

    Hiển thị: tổng điểm, streak, longest streak, rank, ontime/early count.
    """
    user = get_active_user_or_none(update.effective_user.id)
    if not user:
        await update.message.reply_text(
            "❌ Bạn chưa đăng ký hoặc chưa được duyệt.\nGõ /start để đăng ký."
        )
        return

    stats = get_user_stats(user["id"])

    total_pts = stats.get("total_points", 0)
    current_streak = stats.get("current_streak", 0)
    longest_streak = stats.get("longest_streak", 0)
    rank = stats.get("rank", "?")
    ontime = stats.get("ontime_count", 0)
    early = stats.get("early_count", 0)
    streak_label = stats.get("streak_label", "")

    text = (
        f"📊 **THỐNG KÊ CỦA BẠN**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 {user['full_name']}\n\n"
        f"🎯 Tổng điểm: **{total_pts}** pts\n"
        f"🏅 Xếp hạng: **#{rank}**\n\n"
        f"{streak_label}\n"
        f"🔥 Streak hiện tại: **{current_streak}** ngày\n"
        f"⭐ Streak dài nhất: **{longest_streak}** ngày\n\n"
        f"✅ Đi đúng giờ: **{ontime}** lần\n"
        f"🐦 Đi sớm: **{early}** lần\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💡 Gõ /leaderboard để xem bảng xếp hạng."
    )

    await update.message.reply_text(text, parse_mode="Markdown")


# ------------------------------------------------------------------
# B4: Streak Display Helper
# ------------------------------------------------------------------


def format_gamification_line(gami_result: dict) -> str:
    """Format dòng gamification cho check-in response message.

    Tạo 1 dòng streak + points để các check-in handlers append
    vào message response sau check-in thành công.

    Args:
        gami_result: dict từ process_gamification_after_checkin().
            Keys: points_earned, streak_info, is_first_today, first_bonus.

    Returns:
        str: Dòng gamification formatted. Ví dụ:
            "🔥 Streak: 5 ngày | +15 pts"
            Nếu milestone: thêm dòng congratulations.
            Nếu first today: thêm "🥇 Người đầu tiên hôm nay!"
    """
    lines = []
    points = gami_result.get("points_earned", 0)
    streak_info = gami_result.get("streak_info")
    is_first = gami_result.get("is_first_today", False)

    # Streak + points line
    if streak_info:
        current = streak_info.get("current_streak", 0)
        lines.append(f"🔥 Streak: {current} ngày | +{points} pts")

        # Milestone bonus
        milestone_bonus = streak_info.get("milestone_bonus", 0)
        milestone_label = streak_info.get("milestone_label")
        if milestone_bonus > 0 and milestone_label:
            lines.append(
                f"🎉 {milestone_label}! Streak bonus +{milestone_bonus} pts"
            )
    elif points > 0:
        lines.append(f"🎁 +{points} pts")

    # First checkin today
    if is_first:
        first_bonus = gami_result.get("first_bonus", 0)
        bonus_str = f" (+{first_bonus} pts)" if first_bonus > 0 else ""
        lines.append(f"🥇 Người đầu tiên hôm nay!{bonus_str}")

    return "\n".join(lines)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _get_user_names_by_ids(user_ids: list[int]) -> dict[int, str]:
    """Lấy mapping user_id → full_name cho danh sách user IDs.

    Batch query để tránh N+1 problem.

    Args:
        user_ids: List of user IDs (bảng users.id).

    Returns:
        dict: {user_id: full_name}.
    """
    if not user_ids:
        return {}

    # Lấy tất cả users rồi filter (PostgREST không hỗ trợ IN query dễ dàng)
    all_users = db.select("users", columns="id,full_name")
    id_set = set(user_ids)
    return {
        u["id"]: u.get("full_name", f"User #{u['id']}")
        for u in all_users
        if u["id"] in id_set
    }


# ------------------------------------------------------------------
# Handler factories
# ------------------------------------------------------------------


def get_gamification_handlers() -> list:
    """Trả về gamification command handlers.

    Returns:
        list: [leaderboard handler, points handler].
    """
    return [
        CommandHandler(["leaderboard", "xh"], leaderboard_command),
        CommandHandler(["points", "diem"], points_command),
    ]
