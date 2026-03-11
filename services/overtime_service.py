"""Pyng — Overtime Service.

Tính và quản lý overtime (OT) cho nhân viên.

Business rules:
    - OT chỉ tính khi checkout > WORK_END + 30 phút grace period
    - OT cap tại 4 giờ/ngày (240 phút) — tránh quên checkout
    - OT = checkout_time - (WORK_END + 30min)

Ví dụ (WORK_END = 17:45):
    - Checkout 18:00 → 0 phút OT (18:00 < 18:15 grace)
    - Checkout 19:00 → 45 phút OT (19:00 - 18:15 = 45)
    - Checkout 23:30 → 240 phút OT (cap 4h)

Dependencies:
    - db/client — PostgREST queries
    - config/settings — WORK_END
    - config/timezone — timezone helper
"""

import logging
from datetime import date, datetime, timedelta

from db import client as db
from config.settings import WORK_END
from config.timezone import get_tz

logger = logging.getLogger(__name__)

# OT cap: tối đa 4 giờ/ngày (phút)
OT_CAP_MINUTES = 240

# Grace period: 30 phút sau WORK_END mới bắt đầu tính OT
OT_GRACE_MINUTES = 30


def _get_work_end_datetime(target_date: date) -> datetime:
    """Tạo datetime cho WORK_END của ngày cụ thể.

    Args:
        target_date: Ngày cần tính.

    Returns:
        datetime: WORK_END datetime (timezone-aware).
    """
    tz = get_tz()
    parts = WORK_END.split(":")
    hour = int(parts[0])
    minute = int(parts[1])
    return datetime(
        target_date.year, target_date.month, target_date.day,
        hour, minute, 0, tzinfo=tz,
    )


def _date_range(target_date: date) -> tuple[str, str]:
    """Trả về (start, end) ISO string cho 1 ngày cụ thể.

    Args:
        target_date: Ngày cần lấy range.

    Returns:
        tuple: (start_iso, end_iso).
    """
    tz = get_tz()
    start = datetime(
        target_date.year, target_date.month, target_date.day,
        0, 0, 0, tzinfo=tz,
    )
    end = start + timedelta(days=1)
    return start.isoformat(), end.isoformat()


# ------------------------------------------------------------------
# Core: Calculate Overtime
# ------------------------------------------------------------------

def calculate_overtime(user_id: int, target_date: date) -> dict:
    """Tính overtime cho 1 user trong 1 ngày.

    So sánh checkout time với WORK_END + 30 phút grace.
    OT = checkout - (WORK_END + grace), cap 4h.

    Args:
        user_id: ID user trong bảng users.
        target_date: Ngày cần tính OT.

    Returns:
        dict: {
            "date": str,
            "minutes": int — số phút OT (0 nếu không có),
            "checkout_time": str | None — thời gian checkout,
            "has_overtime": bool,
        }
    """
    start_iso, end_iso = _date_range(target_date)
    tz = get_tz()

    # Lấy checkout record (type='out') mới nhất trong ngày
    checkouts = db.select(
        "checkins",
        columns="id,checked_at",
        filters={
            "user_id": user_id,
            "type": "out",
            "checked_at.gte": start_iso,
            "checked_at.lt": end_iso,
        },
        order="checked_at.desc",
        limit=1,
    )

    if not checkouts:
        return {
            "date": target_date.isoformat(),
            "minutes": 0,
            "checkout_time": None,
            "has_overtime": False,
        }

    checkout_str = checkouts[0]["checked_at"]
    checkout_dt = datetime.fromisoformat(checkout_str)
    if checkout_dt.tzinfo is None:
        checkout_dt = checkout_dt.replace(tzinfo=tz)

    # Tính OT threshold = WORK_END + 30 phút grace
    work_end_dt = _get_work_end_datetime(target_date)
    ot_threshold = work_end_dt + timedelta(minutes=OT_GRACE_MINUTES)

    if checkout_dt <= ot_threshold:
        # Checkout trong grace period → không có OT
        return {
            "date": target_date.isoformat(),
            "minutes": 0,
            "checkout_time": checkout_str,
            "has_overtime": False,
        }

    # Tính OT minutes (từ threshold đến checkout)
    ot_delta = checkout_dt - ot_threshold
    ot_minutes = int(ot_delta.total_seconds() / 60)

    # Cap tại OT_CAP_MINUTES
    ot_minutes = min(ot_minutes, OT_CAP_MINUTES)

    return {
        "date": target_date.isoformat(),
        "minutes": ot_minutes,
        "checkout_time": checkout_str,
        "has_overtime": True,
    }


# ------------------------------------------------------------------
# Monthly Overtime
# ------------------------------------------------------------------

def get_monthly_overtime(user_id: int, month: int, year: int) -> dict:
    """Tổng hợp OT tháng cho 1 user.

    Args:
        user_id: ID user.
        month: Tháng (1-12).
        year: Năm.

    Returns:
        dict: {
            "total_minutes": int,
            "total_days": int — số ngày có OT,
            "sessions": list[dict] — [{date, minutes, checkout_time}],
        }
    """
    # Tính ngày đầu/cuối tháng
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    sessions = []
    total_minutes = 0

    current = first_day
    while current <= last_day:
        # Chỉ tính ngày làm việc (Mon-Fri)
        if current.weekday() < 5:
            result = calculate_overtime(user_id, current)
            if result["has_overtime"]:
                sessions.append({
                    "date": result["date"],
                    "minutes": result["minutes"],
                    "checkout_time": result["checkout_time"],
                })
                total_minutes += result["minutes"]

        current += timedelta(days=1)

    return {
        "total_minutes": total_minutes,
        "total_days": len(sessions),
        "sessions": sessions,
    }


# ------------------------------------------------------------------
# Overtime Report (all users)
# ------------------------------------------------------------------

def get_overtime_report(month: int, year: int) -> dict:
    """Tổng hợp OT toàn bộ nhân viên trong tháng.

    Args:
        month: Tháng (1-12).
        year: Năm.

    Returns:
        dict: {
            "month": int,
            "year": int,
            "users": list[dict] — [{user_id, full_name, total_minutes, total_days}],
            "grand_total_minutes": int,
        }
    """
    # Lấy tất cả active users
    all_users = db.select("users", filters={"is_active": True})

    users_ot = []
    grand_total = 0

    for user in all_users:
        ot_data = get_monthly_overtime(user["id"], month, year)
        if ot_data["total_minutes"] > 0:
            users_ot.append({
                "user_id": user["id"],
                "full_name": user.get("full_name", ""),
                "total_minutes": ot_data["total_minutes"],
                "total_days": ot_data["total_days"],
            })
            grand_total += ot_data["total_minutes"]

    return {
        "month": month,
        "year": year,
        "users": users_ot,
        "grand_total_minutes": grand_total,
    }
