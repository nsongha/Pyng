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
    tz = get_tz()
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    month_start = datetime(
        first_day.year, first_day.month, first_day.day,
        0, 0, 0, tzinfo=tz,
    ).isoformat()
    month_end = datetime(
        last_day.year, last_day.month, last_day.day,
        23, 59, 59, tzinfo=tz,
    ).isoformat()

    # Batch query: lấy TẤT CẢ checkouts trong tháng bằng 1 request
    # (trước đây loop theo từng ngày → N+1 query)
    all_checkouts = db.select(
        "checkins",
        columns="checked_at",
        filters={
            "user_id": user_id,
            "type": "out",
            "checked_at.gte": month_start,
            "checked_at.lt": month_end,
        },
        order="checked_at.desc",
    )

    # Gom theo ngày, giữ checkout mới nhất (đã sort desc)
    latest_checkout_by_date: dict[str, str] = {}
    for co in all_checkouts:
        co_dt = datetime.fromisoformat(co["checked_at"])
        if co_dt.tzinfo is None:
            co_dt = co_dt.replace(tzinfo=tz)
        date_key = co_dt.strftime("%Y-%m-%d")
        if date_key not in latest_checkout_by_date:
            latest_checkout_by_date[date_key] = co["checked_at"]

    sessions = []
    total_minutes = 0
    current = first_day

    while current <= last_day:
        if current.weekday() < 5:  # Mon-Fri
            date_key = current.isoformat()
            co_str = latest_checkout_by_date.get(date_key)

            if co_str:
                checkout_dt = datetime.fromisoformat(co_str)
                if checkout_dt.tzinfo is None:
                    checkout_dt = checkout_dt.replace(tzinfo=tz)

                work_end_dt = _get_work_end_datetime(current)
                ot_threshold = work_end_dt + timedelta(minutes=OT_GRACE_MINUTES)

                if checkout_dt > ot_threshold:
                    ot_minutes = int((checkout_dt - ot_threshold).total_seconds() / 60)
                    ot_minutes = min(ot_minutes, OT_CAP_MINUTES)
                    sessions.append({
                        "date": date_key,
                        "minutes": ot_minutes,
                        "checkout_time": co_str,
                    })
                    total_minutes += ot_minutes

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
