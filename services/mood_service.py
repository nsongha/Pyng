"""Pyng — Mood Service.

Quản lý mood tracking: ghi nhận mood sau check-in,
thống kê mood, phát hiện burnout.

Mood types: 'great' | 'good' | 'tired' | 'sos'
  - great = 🔥 Siêu năng suất
  - good  = 😊 Bình thường
  - tired = 😴 Hơi mệt
  - sos   = 🆘 Cần hỗ trợ

Xem docs/GAMIFICATION_DESIGN.md §7.
"""

from datetime import datetime, timedelta

from db import client as db
from config.timezone import get_tz


# Mood labels for display
MOOD_LABELS: dict[str, str] = {
    "great": "🔥 Siêu năng suất",
    "good": "😊 Bình thường",
    "tired": "😴 Hơi mệt",
    "sos": "🆘 Cần hỗ trợ",
}

# Mood tốt → bonus points
POSITIVE_MOODS = {"great", "good"}
MOOD_BONUS_POINTS = 2

# Burnout threshold: N ngày liên tiếp SOS
BURNOUT_CONSECUTIVE_DAYS = 3


# ------------------------------------------------------------------
# Record Mood
# ------------------------------------------------------------------

def record_mood(user_id: int, checkin_id: int, mood: str) -> dict | None:
    """Ghi nhận mood vào checkin record.

    Cập nhật field `mood` trong bảng checkins cho record tương ứng.
    Nếu mood tốt (great/good), cộng bonus points qua gamification_service.

    Args:
        user_id: ID user.
        checkin_id: ID checkin record.
        mood: 'great' | 'good' | 'tired' | 'sos'.

    Returns:
        dict | None: Updated checkin record, None nếu không tìm thấy.
    """
    result = db.update(
        "checkins",
        {"mood": mood},
        filters={"id": checkin_id, "user_id": user_id},
    )

    # Mood tốt → bonus points
    if mood in POSITIVE_MOODS:
        # Import lazily để tránh circular import
        from services.gamification_service import add_points
        add_points(user_id, MOOD_BONUS_POINTS, f"mood_{mood}")

    return result


# ------------------------------------------------------------------
# Mood Stats
# ------------------------------------------------------------------

def get_mood_stats(period: str = "week") -> dict:
    """Thống kê mood aggregate cho toàn team.

    Args:
        period: 'week' hoặc 'month'.

    Returns:
        dict: {
            "total": int,
            "breakdown": {
                "great": {"count": int, "percentage": float},
                "good": {"count": int, "percentage": float},
                "tired": {"count": int, "percentage": float},
                "sos": {"count": int, "percentage": float},
            },
            "period": str,
            "start_date": str,
            "end_date": str,
        }
    """
    tz = get_tz()
    now = datetime.now(tz)

    if period == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            end = start.replace(year=now.year + 1, month=1)
        else:
            end = start.replace(month=now.month + 1)
    else:
        # week — từ thứ 2 tuần này
        days_since_monday = now.weekday()  # 0=Monday
        start = (now - timedelta(days=days_since_monday)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end = start + timedelta(days=7)

    # Lấy tất cả check-in có mood trong khoảng thời gian
    rows = db.select(
        "checkins",
        columns="mood",
        filters={
            "type": "in",
            "mood.neq": "null",
            "checked_at.gte": start.isoformat(),
            "checked_at.lt": end.isoformat(),
        },
    )

    # Filter out rows without mood (PostgREST neq null có thể không hoạt động)
    rows = [r for r in rows if r.get("mood")]

    total = len(rows)
    breakdown: dict[str, dict] = {}
    for mood_type in ["great", "good", "tired", "sos"]:
        count = sum(1 for r in rows if r["mood"] == mood_type)
        percentage = round(count / total * 100, 1) if total > 0 else 0.0
        breakdown[mood_type] = {
            "count": count,
            "percentage": percentage,
        }

    return {
        "total": total,
        "breakdown": breakdown,
        "period": period,
        "start_date": start.strftime("%d/%m/%Y"),
        "end_date": end.strftime("%d/%m/%Y"),
    }


# ------------------------------------------------------------------
# Burnout Detection
# ------------------------------------------------------------------

def check_burnout_alert(user_id: int) -> bool:
    """Kiểm tra user có dấu hiệu burnout không.

    Burnout = báo cáo 'sos' (Cần hỗ trợ) N ngày liên tiếp.
    Threshold mặc định: 3 ngày.

    Args:
        user_id: ID user.

    Returns:
        bool: True nếu phát hiện burnout pattern.
    """
    tz = get_tz()
    now = datetime.now(tz)

    # Lấy mood gần nhất theo ngày (N ngày gần nhất)
    start = (now - timedelta(days=BURNOUT_CONSECUTIVE_DAYS + 1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    rows = db.select(
        "checkins",
        columns="mood,checked_at",
        filters={
            "user_id": user_id,
            "type": "in",
            "checked_at.gte": start.isoformat(),
        },
        order="checked_at.desc",
        limit=BURNOUT_CONSECUTIVE_DAYS,
    )

    if len(rows) < BURNOUT_CONSECUTIVE_DAYS:
        return False

    # Kiểm tra tất cả đều là 'sos'
    return all(r.get("mood") == "sos" for r in rows)


# ------------------------------------------------------------------
# User Mood History
# ------------------------------------------------------------------

def get_user_mood_history(user_id: int, days: int = 30) -> list[dict]:
    """Lấy lịch sử mood của user trong N ngày gần nhất.

    Args:
        user_id: ID user.
        days: Số ngày lấy (default 30).

    Returns:
        list[dict]: Danh sách {date, mood, mood_label},
                    sorted theo ngày mới nhất trước.
    """
    tz = get_tz()
    now = datetime.now(tz)
    start = (now - timedelta(days=days)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    rows = db.select(
        "checkins",
        columns="checked_at,mood",
        filters={
            "user_id": user_id,
            "type": "in",
            "checked_at.gte": start.isoformat(),
        },
        order="checked_at.desc",
    )

    result = []
    for row in rows:
        mood = row.get("mood")
        if mood:
            result.append({
                "date": row["checked_at"],
                "mood": mood,
                "mood_label": MOOD_LABELS.get(mood, mood),
            })

    return result
