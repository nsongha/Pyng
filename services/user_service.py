"""Pyng — User Service.

CRUD operations cho bảng `users`.
Business logic: đăng ký, duyệt, kiểm tra admin.
"""

from db import client as db
from config.settings import ADMIN_TELEGRAM_IDS


def register_user(
    telegram_id: int,
    telegram_username: str | None,
    full_name: str,
    email: str,
) -> dict:
    """Đăng ký user mới (trạng thái pending = is_active False).

    Returns:
        dict: User record vừa tạo.

    Raises:
        Exception: Nếu user đã tồn tại (telegram_id unique constraint).
    """
    return db.insert("users", {
        "telegram_id": telegram_id,
        "telegram_username": telegram_username,
        "full_name": full_name,
        "email": email,
        "is_active": False,  # pending, chờ admin duyệt
    })


def get_by_telegram_id(telegram_id: int) -> dict | None:
    """Tìm user theo telegram_id.

    Returns:
        dict | None: User record hoặc None nếu không tìm thấy.
    """
    rows = db.select("users", filters={"telegram_id": telegram_id})
    return rows[0] if rows else None


def activate_user(telegram_id: int) -> dict | None:
    """Duyệt user — set is_active = True.

    Returns:
        dict | None: Updated user record.
    """
    return db.update(
        "users",
        {"is_active": True},
        filters={"telegram_id": telegram_id},
    )


def reject_user(telegram_id: int) -> bool:
    """Từ chối user — xóa record khỏi DB.

    Returns:
        bool: True nếu xóa thành công.
    """
    deleted = db.delete(
        "users",
        filters={"telegram_id": telegram_id, "is_active": False},
    )
    return len(deleted) > 0


def is_admin(telegram_id: int) -> bool:
    """Kiểm tra user có phải admin không.

    Check theo ADMIN_TELEGRAM_IDS trong config (env var).
    """
    return telegram_id in ADMIN_TELEGRAM_IDS


def get_all_active_users() -> list[dict]:
    """Lấy danh sách tất cả active users.

    Returns:
        list[dict]: List of active user records.
    """
    return db.select("users", filters={"is_active": True})
