"""Pyng — Config Service.

CRUD operations cho bảng `system_config`.
Key-value store cho cấu hình hệ thống (giờ làm, toggle methods, etc.).

Keys dự kiến:
    - work_start: Giờ bắt đầu làm việc (vd "08:45")
    - work_end: Giờ kết thúc (vd "17:45")
    - late_budget_minutes: Quỹ đi muộn tháng (vd "180")
    - checkin_methods_enabled: JSON array (vd '["gps","wifi","qr","nfc","manual"]')
"""

from datetime import datetime

from db import client as db
from config.timezone import get_tz


def get_config(key: str) -> str | None:
    """Lấy value của config theo key.

    Args:
        key: Config key (vd "work_start").

    Returns:
        str | None: Config value, hoặc None nếu key chưa tồn tại.
    """
    rows = db.select("system_config", filters={"key": key}, limit=1)
    return rows[0]["value"] if rows else None


def set_config(key: str, value: str, updated_by: int) -> dict:
    """Upsert config: insert nếu chưa có, update nếu đã tồn tại.

    Args:
        key: Config key.
        value: Config value (luôn lưu dạng string).
        updated_by: Telegram ID của admin thực hiện thay đổi.

    Returns:
        dict: Config record sau khi upsert.
    """
    tz = get_tz()
    now = datetime.now(tz).isoformat()

    existing = db.select("system_config", filters={"key": key}, limit=1)

    if existing:
        return db.update(
            "system_config",
            {"value": value, "updated_by": updated_by, "updated_at": now},
            filters={"key": key},
        )

    return db.insert("system_config", {
        "key": key,
        "value": value,
        "updated_by": updated_by,
        "updated_at": now,
    })


def get_all_configs() -> list[dict]:
    """Lấy tất cả config records.

    Returns:
        list[dict]: Danh sách config records, sorted theo key.
    """
    return db.select("system_config", order="key.asc")
