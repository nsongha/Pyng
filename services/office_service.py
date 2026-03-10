"""Pyng — Office Service.

CRUD operations cho bảng `offices` và `wifi_whitelist`.
"""

from db import client as db


def get_active_office() -> dict | None:
    """Lấy office đầu tiên đang active.

    Returns:
        dict | None: Office record hoặc None.
    """
    rows = db.select("offices", filters={"is_active": True}, limit=1)
    return rows[0] if rows else None


def update_geofence_radius(office_id: int, radius_m: int) -> dict | None:
    """Cập nhật bán kính geofence cho office.

    Args:
        office_id: ID office.
        radius_m: Bán kính mới (mét).

    Returns:
        dict | None: Updated office record.
    """
    return db.update(
        "offices",
        {"radius_m": radius_m},
        filters={"id": office_id},
    )


def get_wifi_whitelist(office_id: int | None = None) -> list[dict]:
    """Lấy danh sách WiFi whitelist.

    Args:
        office_id: Filter theo office (optional, None = all).

    Returns:
        list[dict]: List of WiFi whitelist records.
    """
    filters: dict = {"is_active": True}
    if office_id is not None:
        filters["office_id"] = office_id

    return db.select("wifi_whitelist", filters=filters)


def add_wifi_ssid(
    office_id: int,
    ssid: str,
    added_by: int,
    description: str | None = None,
) -> dict:
    """Thêm SSID vào whitelist.

    Args:
        office_id: ID office.
        ssid: Tên WiFi.
        added_by: telegram_id của admin.
        description: Mô tả (optional).

    Returns:
        dict: Record vừa tạo.
    """
    data = {
        "office_id": office_id,
        "ssid": ssid,
        "added_by": added_by,
    }
    if description:
        data["description"] = description

    return db.insert("wifi_whitelist", data)


def remove_wifi_ssid(ssid_id: int) -> bool:
    """Xóa SSID khỏi whitelist (soft delete — set is_active = False).

    Args:
        ssid_id: ID record trong bảng wifi_whitelist.

    Returns:
        bool: True nếu xóa thành công.
    """
    result = db.update(
        "wifi_whitelist",
        {"is_active": False},
        filters={"id": ssid_id},
    )
    return result is not None
