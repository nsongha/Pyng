"""Pyng — Checkin Service.

CRUD operations cho bảng `checkins`.
Business logic: check-in, check-out, WFH, duplicate check, working hours.
"""

from datetime import datetime, timedelta

from db.client import get_client
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

    Returns:
        dict: Checkin record vừa tạo.
    """
    client = get_client()
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

    result = client.table("checkins").insert(data).execute()
    return result.data[0] if result.data else {}


def get_today_checkin(user_id: int, checkin_type: str = "in") -> dict | None:
    """Lấy checkin hôm nay của user.

    Args:
        user_id: ID user.
        checkin_type: 'in' hoặc 'out'.

    Returns:
        dict | None: Checkin record hoặc None.
    """
    client = get_client()
    start, end = _today_range()
    result = (
        client.table("checkins")
        .select("*")
        .eq("user_id", user_id)
        .eq("type", checkin_type)
        .gte("checked_at", start)
        .lt("checked_at", end)
        .order("checked_at", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


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
    client = get_client()
    start, end = _current_month_range()
    result = (
        client.table("checkins")
        .select("id", count="exact")
        .eq("user_id", user_id)
        .eq("type", "in")
        .eq("method", "wfh")
        .gte("checked_at", start)
        .lt("checked_at", end)
        .execute()
    )
    return result.count or 0


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
