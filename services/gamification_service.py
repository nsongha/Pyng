"""Pyng — Gamification Service.

CRUD operations cho bảng `gamification` + `point_transactions`.
Business logic: tính điểm check-in, streak management, leaderboard.

Hệ thống điểm (xem docs/GAMIFICATION_DESIGN.md):
  - Check-in đúng giờ: +10
  - Check-in sớm (≥15 phút): +15
  - Check-in muộn ≤30 phút: +5
  - Check-in muộn >30 phút: +2
  - WFH check-in: +8
  - Check-out đúng giờ: +5
  - Mood tốt (great/good): +2  (gọi từ mood_service)
  - Người đầu tiên check-in: +5
  - Streak milestones: 5→+20, 10→+50, 20→+100, 30→+200
"""

from datetime import datetime, timedelta

from db import client as db
from config.timezone import get_tz
from config.settings import WORK_END


# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------

STREAK_MILESTONES: dict[int, int] = {
    5: 20,
    10: 50,
    20: 100,
    30: 200,
}

# Điểm theo loại check-in
POINTS_CHECKIN_ONTIME = 10
POINTS_CHECKIN_EARLY = 15
POINTS_CHECKIN_LATE_WITHIN_30 = 5
POINTS_CHECKIN_LATE_OVER_30 = 2
POINTS_CHECKIN_WFH = 8
POINTS_CHECKOUT_ONTIME = 5
POINTS_FIRST_CHECKIN = 5


# ------------------------------------------------------------------
# CRUD — Gamification record
# ------------------------------------------------------------------

def get_or_create_gamification(user_id: int) -> dict:
    """Lấy hoặc tạo record gamification cho user.

    Args:
        user_id: ID user (bảng users.id).

    Returns:
        dict: Gamification record.
    """
    rows = db.select("gamification", filters={"user_id": user_id}, limit=1)
    if rows:
        return rows[0]

    return db.insert("gamification", {
        "user_id": user_id,
        "total_points": 0,
        "current_streak": 0,
        "longest_streak": 0,
        "ontime_count": 0,
        "early_count": 0,
    })


def add_points(user_id: int, points: int, reason: str) -> dict:
    """Cộng điểm cho user + tạo transaction log.

    Cập nhật total_points trong bảng gamification,
    đồng thời tạo record trong point_transactions.

    Args:
        user_id: ID user.
        points: Số điểm cộng (luôn >= 0, hệ thống không trừ điểm).
        reason: Lý do nhận điểm (vd: 'checkin_ontime', 'streak_5').

    Returns:
        dict: Point transaction record vừa tạo.
    """
    if points <= 0:
        return {}

    # Tạo transaction log
    transaction = db.insert("point_transactions", {
        "user_id": user_id,
        "points": points,
        "reason": reason,
    })

    # Cập nhật total_points trong gamification
    gami = get_or_create_gamification(user_id)
    new_total = gami.get("total_points", 0) + points
    db.update(
        "gamification",
        {"total_points": new_total, "updated_at": datetime.now(get_tz()).isoformat()},
        filters={"user_id": user_id},
    )

    return transaction


# ------------------------------------------------------------------
# Tính điểm check-in
# ------------------------------------------------------------------

def calculate_checkin_points(
    user_id: int,
    checkin_type: str,
    *,
    is_ontime: bool = False,
    is_early: bool = False,
    is_wfh: bool = False,
    late_minutes: int = 0,
) -> int:
    """Tính điểm check-in theo GAMIFICATION_DESIGN.md.

    Args:
        user_id: ID user.
        checkin_type: 'in' hoặc 'out'.
        is_ontime: True nếu check-in đúng giờ (≤5 phút grace).
        is_early: True nếu check-in sớm ≥15 phút.
        is_wfh: True nếu WFH check-in.
        late_minutes: Số phút muộn (chỉ relevant khi không ontime/early).

    Returns:
        int: Số điểm được cộng.
    """
    points = 0

    if checkin_type == "in":
        if is_wfh:
            points = POINTS_CHECKIN_WFH
        elif is_early:
            points = POINTS_CHECKIN_EARLY
        elif is_ontime:
            points = POINTS_CHECKIN_ONTIME
        elif late_minutes <= 30:
            points = POINTS_CHECKIN_LATE_WITHIN_30
        else:
            points = POINTS_CHECKIN_LATE_OVER_30

        # Update ontime/early count
        if is_ontime or is_early:
            gami = get_or_create_gamification(user_id)
            update_data: dict = {
                "updated_at": datetime.now(get_tz()).isoformat(),
            }
            if is_early:
                update_data["early_count"] = gami.get("early_count", 0) + 1
            if is_ontime or is_early:
                update_data["ontime_count"] = gami.get("ontime_count", 0) + 1
            db.update("gamification", update_data, filters={"user_id": user_id})

    elif checkin_type == "out":
        # Check-out đúng giờ (trước hoặc sau WORK_END ≤15 phút)
        now = datetime.now(get_tz())
        work_end_parts = WORK_END.split(":")
        work_end_minutes = int(work_end_parts[0]) * 60 + int(work_end_parts[1])
        current_minutes = now.hour * 60 + now.minute
        diff = abs(current_minutes - work_end_minutes)
        if diff <= 15:
            points = POINTS_CHECKOUT_ONTIME

    return points


# ------------------------------------------------------------------
# Streak Management
# ------------------------------------------------------------------

def update_streak(user_id: int, action: str) -> dict:
    """Cập nhật streak cho user.

    Args:
        user_id: ID user.
        action: 'checkin' → tăng streak, 'reset' → reset về 0.

    Returns:
        dict: {
            "current_streak": int,
            "longest_streak": int,
            "milestone_bonus": int (0 nếu không đạt milestone),
            "milestone_label": str | None,
        }
    """
    gami = get_or_create_gamification(user_id)
    current = gami.get("current_streak", 0)
    longest = gami.get("longest_streak", 0)
    milestone_bonus = 0
    milestone_label = None

    if action == "checkin":
        current += 1
        if current > longest:
            longest = current

        # Check milestone bonus
        milestone_bonus = check_streak_milestones(current)
        if milestone_bonus > 0:
            milestone_label = _get_streak_label(current)
            add_points(user_id, milestone_bonus, f"streak_{current}")

    elif action == "reset":
        current = 0

    # Update DB
    db.update(
        "gamification",
        {
            "current_streak": current,
            "longest_streak": longest,
            "updated_at": datetime.now(get_tz()).isoformat(),
        },
        filters={"user_id": user_id},
    )

    return {
        "current_streak": current,
        "longest_streak": longest,
        "milestone_bonus": milestone_bonus,
        "milestone_label": milestone_label,
    }


def check_streak_milestones(current_streak: int) -> int:
    """Kiểm tra streak có đạt milestone không.

    Milestones: 5→+20, 10→+50, 20→+100, 30→+200.

    Args:
        current_streak: Streak hiện tại.

    Returns:
        int: Bonus points nếu đạt milestone, 0 nếu không.
    """
    return STREAK_MILESTONES.get(current_streak, 0)


def _get_streak_label(streak: int) -> str:
    """Lấy label hiển thị cho streak level.

    Args:
        streak: Số ngày streak.

    Returns:
        str: Label hiển thị.
    """
    if streak >= 30:
        return "💎 Huyền thoại"
    if streak >= 20:
        return "⚡ Chuyên nghiệp!"
    if streak >= 10:
        return "🔥🔥🔥 Ổn định"
    if streak >= 5:
        return "🔥🔥 Vào guồng rồi!"
    return "🔥 Đang khởi động"


# ------------------------------------------------------------------
# Leaderboard
# ------------------------------------------------------------------

def get_leaderboard(period: str = "month", limit: int = 10) -> list[dict]:
    """Lấy bảng xếp hạng top users.

    Args:
        period: 'month' (tháng này) hoặc 'alltime' (tổng).
        limit: Số lượng users trả về (default 10).

    Returns:
        list[dict]: Danh sách users kèm points, sorted desc.
            Mỗi item: {user_id, total_points, current_streak, ...}
            + join với users table để lấy full_name.
    """
    if period == "month":
        # Tính điểm tháng này từ point_transactions
        tz = get_tz()
        now = datetime.now(tz)
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            end = start.replace(year=now.year + 1, month=1)
        else:
            end = start.replace(month=now.month + 1)

        # PostgREST hỗ trợ aggregate qua RPC hoặc view
        # Vì không có custom RPC, ta lấy transactions tháng này rồi aggregate
        transactions = db.select(
            "point_transactions",
            columns="user_id,points",
            filters={
                "created_at.gte": start.isoformat(),
                "created_at.lt": end.isoformat(),
            },
        )

        # Aggregate points by user_id
        user_points: dict[int, int] = {}
        for tx in transactions:
            uid = tx["user_id"]
            user_points[uid] = user_points.get(uid, 0) + tx["points"]

        # Sort by points desc, take top N
        sorted_users = sorted(user_points.items(), key=lambda x: x[1], reverse=True)
        top_users = sorted_users[:limit]

        # Enrich với gamification data
        result = []
        for rank, (uid, pts) in enumerate(top_users, 1):
            gami_rows = db.select(
                "gamification", filters={"user_id": uid}, limit=1
            )
            gami = gami_rows[0] if gami_rows else {}
            result.append({
                "rank": rank,
                "user_id": uid,
                "month_points": pts,
                "current_streak": gami.get("current_streak", 0),
            })

        return result

    # alltime — order by total_points trong gamification
    rows = db.select(
        "gamification",
        order="total_points.desc",
        limit=limit,
    )
    result = []
    for rank, row in enumerate(rows, 1):
        result.append({
            "rank": rank,
            "user_id": row["user_id"],
            "total_points": row.get("total_points", 0),
            "current_streak": row.get("current_streak", 0),
        })
    return result


# ------------------------------------------------------------------
# User Stats
# ------------------------------------------------------------------

def get_user_stats(user_id: int) -> dict:
    """Lấy thống kê gamification đầy đủ cho user.

    Args:
        user_id: ID user.

    Returns:
        dict: {
            "total_points": int,
            "current_streak": int,
            "longest_streak": int,
            "rank": int,
            "ontime_count": int,
            "early_count": int,
            "streak_label": str,
        }
    """
    gami = get_or_create_gamification(user_id)

    # Tính rank — đếm users có total_points cao hơn
    total_pts = gami.get("total_points", 0)
    all_gami = db.select(
        "gamification",
        columns="user_id,total_points",
        order="total_points.desc",
    )
    rank = 1
    for row in all_gami:
        if row["user_id"] == user_id:
            break
        rank += 1

    current_streak = gami.get("current_streak", 0)

    return {
        "total_points": total_pts,
        "current_streak": current_streak,
        "longest_streak": gami.get("longest_streak", 0),
        "rank": rank,
        "ontime_count": gami.get("ontime_count", 0),
        "early_count": gami.get("early_count", 0),
        "streak_label": _get_streak_label(current_streak),
    }


# ------------------------------------------------------------------
# First Check-in Today
# ------------------------------------------------------------------

def is_first_checkin_today(user_id: int) -> bool:
    """Kiểm tra user có phải người đầu tiên check-in hôm nay không.

    Check bảng checkins: có record type='in' nào hôm nay
    VỚI checked_at sớm hơn không.

    Args:
        user_id: ID user.

    Returns:
        bool: True nếu là người đầu tiên.
    """
    tz = get_tz()
    now = datetime.now(tz)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)

    # Lấy check-in đầu tiên hôm nay (không phải WFH)
    rows = db.select(
        "checkins",
        columns="user_id",
        filters={
            "type": "in",
            "checked_at.gte": start.isoformat(),
            "checked_at.lt": end.isoformat(),
        },
        order="checked_at.asc",
        limit=1,
    )

    if not rows:
        # Chưa ai check-in → user này sẽ là người đầu tiên
        return True

    return rows[0]["user_id"] == user_id
