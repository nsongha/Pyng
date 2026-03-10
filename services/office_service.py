"""Pyng — Office Service.

CRUD operations cho bảng `offices` và `wifi_whitelist`.
"""

from db.client import get_client


def get_active_office() -> dict | None:
    """Lấy office đầu tiên đang active.

    Returns:
        dict | None: Office record hoặc None.
    """
    client = get_client()
    result = (
        client.table("offices")
        .select("*")
        .eq("is_active", True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def update_geofence_radius(office_id: int, radius_m: int) -> dict | None:
    """Cập nhật bán kính geofence cho office.

    Args:
        office_id: ID office.
        radius_m: Bán kính mới (mét).

    Returns:
        dict | None: Updated office record.
    """
    client = get_client()
    result = (
        client.table("offices")
        .update({"radius_m": radius_m})
        .eq("id", office_id)
        .execute()
    )
    return result.data[0] if result.data else None


def get_wifi_whitelist(office_id: int | None = None) -> list[dict]:
    """Lấy danh sách WiFi whitelist.

    Args:
        office_id: Filter theo office (optional, None = all).

    Returns:
        list[dict]: List of WiFi whitelist records.
    """
    client = get_client()
    query = client.table("wifi_whitelist").select("*").eq("is_active", True)

    if office_id is not None:
        query = query.eq("office_id", office_id)

    result = query.execute()
    return result.data or []


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
    client = get_client()
    data = {
        "office_id": office_id,
        "ssid": ssid,
        "added_by": added_by,
    }
    if description:
        data["description"] = description

    result = client.table("wifi_whitelist").insert(data).execute()
    return result.data[0] if result.data else {}


def remove_wifi_ssid(ssid_id: int) -> bool:
    """Xóa SSID khỏi whitelist (soft delete — set is_active = False).

    Args:
        ssid_id: ID record trong bảng wifi_whitelist.

    Returns:
        bool: True nếu xóa thành công.
    """
    client = get_client()
    result = (
        client.table("wifi_whitelist")
        .update({"is_active": False})
        .eq("id", ssid_id)
        .execute()
    )
    return len(result.data) > 0 if result.data else False
