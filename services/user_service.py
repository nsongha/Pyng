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


# ------------------------------------------------------------------
# Phase 3: Admin CRUD operations
# ------------------------------------------------------------------

def get_all_users() -> list[dict]:
    """Lấy danh sách tất cả users (kể cả inactive).

    Returns:
        list[dict]: List of all user records, sorted theo full_name.
    """
    return db.select("users", order="full_name.asc")


def update_user(telegram_id: int, data: dict) -> dict | None:
    """Cập nhật thông tin user.

    Chỉ cho phép update các fields an toàn:
    role, department, is_active, annual_leave_days.

    Args:
        telegram_id: Telegram ID của user cần update.
        data: Dict chứa fields cần update.

    Returns:
        dict | None: Updated user record, hoặc None nếu không tìm thấy.
    """
    allowed_fields = {"role", "department", "is_active", "annual_leave_days"}
    safe_data = {k: v for k, v in data.items() if k in allowed_fields}

    if not safe_data:
        return None

    return db.update("users", safe_data, filters={"telegram_id": telegram_id})


def deactivate_user(telegram_id: int) -> dict | None:
    """Vô hiệu hóa tài khoản user (soft delete).

    Args:
        telegram_id: Telegram ID của user.

    Returns:
        dict | None: Updated user record, hoặc None nếu không tìm thấy.
    """
    return db.update(
        "users",
        {"is_active": False},
        filters={"telegram_id": telegram_id},
    )


def get_users_by_role(role: str) -> list[dict]:
    """Lọc users theo role.

    Args:
        role: 'employee' | 'manager' | 'admin'.

    Returns:
        list[dict]: List of user records matching role.
    """
    return db.select(
        "users",
        filters={"role": role, "is_active": True},
        order="full_name.asc",
    )

