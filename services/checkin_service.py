"""Pyng — Checkin Service.

CRUD operations cho bảng `checkins`.
Business logic: check-in, check-out, WFH, duplicate check, working hours.
"""

from datetime import datetime, timedelta

from db import client as db
from config.settings import WFH_LIMIT_PER_MONTH
from config.timezone import get_tz


def _today_range() -> tuple[str, str]:
    """Trả về (start_of_day, end_of_day) ISO string theo timezone config.

    Returns:
        tuple: (start_iso, end_iso) dạng UTC ISO string.
    """
    tz = get_tz()
    now = datetime.now(tz)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start.isoformat(), end.isoformat()


def _current_month_range() -> tuple[str, str]:
    """Trả về (start_of_month, end_of_month) ISO string.

    Returns:
        tuple: (start_iso, end_iso).
    """
    tz = get_tz()
    now = datetime.now(tz)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # Tháng sau
    if now.month == 12:
        end = start.replace(year=now.year + 1, month=1)
    else:
        end = start.replace(month=now.month + 1)
    return start.isoformat(), end.isoformat()


def create_checkin(
    user_id: int,
    checkin_type: str,
    method: str,
    *,
    office_id: int | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    gps_accuracy_m: int | None = None,
    distance_m: int | None = None,
    wifi_ssid: str | None = None,
    note: str | None = None,
    mood: str | None = None,
) -> dict:
    """Tạo record check-in/check-out.

    Args:
        user_id: ID user trong bảng users.
        checkin_type: 'in' hoặc 'out'.
        method: 'gps' | 'wifi' | 'qr' | 'nfc' | 'manual' | 'wfh'.
        office_id: ID văn phòng (optional).
        latitude, longitude: Tọa độ GPS (optional).
        gps_accuracy_m: Độ chính xác GPS (mét).
        distance_m: Khoảng cách tới văn phòng (mét).
        wifi_ssid: Tên WiFi (nếu method=wifi).
        note: Ghi chú (optional).
        mood: 'great' | 'good' | 'tired' | 'sos' (optional, Phase 4).

    Returns:
        dict: Checkin record vừa tạo.
    """
    data = {
        "user_id": user_id,
        "type": checkin_type,
        "method": method,
        "is_valid": True,
    }

    # Optional fields
    if office_id is not None:
        data["office_id"] = office_id
    if latitude is not None:
        data["latitude"] = latitude
    if longitude is not None:
        data["longitude"] = longitude
    if gps_accuracy_m is not None:
        data["gps_accuracy_m"] = gps_accuracy_m
    if distance_m is not None:
        data["distance_m"] = distance_m
    if wifi_ssid is not None:
        data["wifi_ssid"] = wifi_ssid
    if note is not None:
        data["note"] = note
    if mood is not None:
        data["mood"] = mood

    return db.insert("checkins", data)


def get_today_checkin(user_id: int, checkin_type: str = "in") -> dict | None:
    """Lấy checkin hôm nay của user.

    Args:
        user_id: ID user.
        checkin_type: 'in' hoặc 'out'.

    Returns:
        dict | None: Checkin record hoặc None.
    """
    start, end = _today_range()
    rows = db.select(
        "checkins",
        filters={
            "user_id": user_id,
            "type": checkin_type,
            "checked_at.gte": start,
            "checked_at.lt": end,
        },
        order="checked_at.desc",
        limit=1,
    )
    return rows[0] if rows else None


def has_checked_in_today(user_id: int) -> bool:
    """Kiểm tra user đã check-in hôm nay chưa.

    Returns:
        bool: True nếu đã check-in.
    """
    return get_today_checkin(user_id, "in") is not None


def create_checkout(user_id: int) -> dict:
    """Tạo checkout record và tính working hours.

    Returns:
        dict: {
            "checkout": checkout record,
            "checkin": checkin record sáng nay,
            "working_hours": float (giờ),
            "working_minutes": int (phút),
        }
    """
    checkin = get_today_checkin(user_id, "in")
    if not checkin:
        return {"error": "Bạn chưa check-in hôm nay"}

    # Tạo checkout record
    checkout = create_checkin(user_id, "out", checkin.get("method", "manual"))

    # Tính working hours
    checkin_time = datetime.fromisoformat(checkin["checked_at"])
    checkout_time = datetime.fromisoformat(checkout["checked_at"])
    diff = checkout_time - checkin_time
    hours = diff.total_seconds() / 3600
    minutes = int(diff.total_seconds() / 60)

    return {
        "checkout": checkout,
        "checkin": checkin,
        "working_hours": round(hours, 1),
        "working_minutes": minutes,
    }


def get_wfh_count_this_month(user_id: int) -> int:
    """Đếm số lần WFH trong tháng hiện tại.

    Returns:
        int: Số lần WFH.
    """
    start, end = _current_month_range()
    return db.select(
        "checkins",
        columns="id",
        filters={
            "user_id": user_id,
            "type": "in",
            "method": "wfh",
            "checked_at.gte": start,
            "checked_at.lt": end,
        },
        count=True,
    )


def create_wfh_checkin(user_id: int, note: str | None = None) -> dict:
    """Tạo WFH check-in.

    Args:
        user_id: ID user.
        note: Ghi chú (optional).

    Returns:
        dict: {"checkin": record, "wfh_count": int, "wfh_limit": int}
              hoặc {"error": str} nếu vượt limit.
    """
    wfh_count = get_wfh_count_this_month(user_id)

    if wfh_count >= WFH_LIMIT_PER_MONTH:
        return {
            "error": f"Bạn đã dùng hết {WFH_LIMIT_PER_MONTH} lần WFH trong tháng này",
            "wfh_count": wfh_count,
            "wfh_limit": WFH_LIMIT_PER_MONTH,
        }

    checkin = create_checkin(user_id, "in", "wfh", note=note)
    return {
        "checkin": checkin,
        "wfh_count": wfh_count + 1,
        "wfh_limit": WFH_LIMIT_PER_MONTH,
    }


# ------------------------------------------------------------------
# Phase 4: Gamification Integration
# ------------------------------------------------------------------

def process_gamification_after_checkin(
    user_id: int,
    checkin_type: str,
    *,
    is_ontime: bool = False,
    is_early: bool = False,
    is_wfh: bool = False,
    late_minutes: int = 0,
) -> dict:
    """Xử lý gamification sau khi check-in thành công.

    Orchestrator gọi gamification_service để:
    1. Tính điểm check-in
    2. Cộng điểm
    3. Cập nhật streak (chỉ khi check-in sáng)
    4. Check first-of-day bonus

    Handler (Wave 2) gọi hàm này sau mỗi check-in thành công.
    KHÔNG gọi tự động trong create_checkin() để giữ flexibility.

    Args:
        user_id: ID user.
        checkin_type: 'in' hoặc 'out'.
        is_ontime: Đúng giờ (≤5 phút grace).
        is_early: Sớm ≥15 phút.
        is_wfh: WFH check-in.
        late_minutes: Số phút muộn.

    Returns:
        dict: {
            "points_earned": int,
            "reason": str,
            "streak_info": dict | None (chỉ khi type='in'),
            "is_first_today": bool,
            "first_bonus": int,
        }
    """
    from services.gamification_service import (
        calculate_checkin_points,
        add_points,
        update_streak,
        is_first_checkin_today,
    )

    # 1. Tính điểm check-in
    points = calculate_checkin_points(
        user_id,
        checkin_type,
        is_ontime=is_ontime,
        is_early=is_early,
        is_wfh=is_wfh,
        late_minutes=late_minutes,
    )

    # 2. Xác định reason
    if is_wfh:
        reason = "checkin_wfh"
    elif is_early:
        reason = "checkin_early"
    elif is_ontime:
        reason = "checkin_ontime"
    elif checkin_type == "out":
        reason = "checkout"
    else:
        reason = f"checkin_late_{late_minutes}min"

    # 3. Cộng điểm
    if points > 0:
        add_points(user_id, points, reason)

    # 4. Streak + first-of-day (chỉ check-in sáng)
    streak_info = None
    is_first = False
    first_bonus = 0

    if checkin_type == "in":
        streak_info = update_streak(user_id, "checkin")

        # Check first checkin today
        is_first = is_first_checkin_today(user_id)
        if is_first:
            from services.gamification_service import POINTS_FIRST_CHECKIN
            first_bonus = POINTS_FIRST_CHECKIN
            add_points(user_id, first_bonus, "first_checkin_today")

    return {
        "points_earned": points + first_bonus,
        "reason": reason,
        "streak_info": streak_info,
        "is_first_today": is_first,
        "first_bonus": first_bonus,
    }
