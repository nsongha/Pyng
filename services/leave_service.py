"""Pyng — Leave Service.

CRUD operations cho bảng `leaves`.
Business logic: tạo đơn nghỉ, duyệt/từ chối, tính ngày phép còn lại.

Leave types:
    - annual: Nghỉ phép năm (trừ annual_leave_days khi approve)
    - compensatory: Nghỉ bù
    - unpaid: Nghỉ không lương
    - sick: Nghỉ ốm
"""

from datetime import date, datetime, timedelta

from db import client as db
from config.timezone import get_tz


def _count_business_days(start_date: date, end_date: date) -> float:
    """Đếm số ngày làm việc (trừ T7, CN) giữa 2 ngày (inclusive).

    Args:
        start_date: Ngày bắt đầu.
        end_date: Ngày kết thúc.

    Returns:
        float: Số ngày làm việc.
    """
    if end_date < start_date:
        return 0

    count = 0
    current = start_date
    while current <= end_date:
        # weekday(): 0=Mon ... 6=Sun
        if current.weekday() < 5:  # Mon-Fri
            count += 1
        current += timedelta(days=1)
    return float(count)


def create_leave_request(
    user_id: int,
    leave_type: str,
    start_date: date,
    end_date: date,
    reason: str | None = None,
) -> dict:
    """Tạo đơn xin nghỉ mới (status = pending).

    Tự động tính days_count (business days only).

    Args:
        user_id: ID user trong bảng users.
        leave_type: 'annual' | 'compensatory' | 'unpaid' | 'sick'.
        start_date: Ngày bắt đầu nghỉ.
        end_date: Ngày kết thúc nghỉ.
        reason: Lý do nghỉ (optional).

    Returns:
        dict: Leave record vừa tạo.
    """
    days_count = _count_business_days(start_date, end_date)

    data = {
        "user_id": user_id,
        "leave_type": leave_type,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "days_count": days_count,
        "status": "pending",
    }
    if reason:
        data["reason"] = reason

    return db.insert("leaves", data)


def approve_leave(leave_id: int, approved_by_id: int) -> dict | None:
    """Duyệt đơn nghỉ.

    Nếu leave_type = 'annual' → trừ annual_leave_days của user.

    Args:
        leave_id: ID đơn nghỉ.
        approved_by_id: ID user (admin/manager) duyệt.

    Returns:
        dict | None: Leave record đã update, hoặc None nếu không tìm thấy.
    """
    tz = get_tz()
    now = datetime.now(tz).isoformat()

    # Update leave status
    leave = db.update(
        "leaves",
        {
            "status": "approved",
            "approved_by": approved_by_id,
            "processed_at": now,
        },
        filters={"id": leave_id, "status": "pending"},
    )

    if not leave:
        return None

    # Trừ ngày phép nếu loại 'annual'
    if leave.get("leave_type") == "annual":
        days = float(leave.get("days_count", 0))
        user_id = leave["user_id"]

        # Lấy user hiện tại
        users = db.select("users", filters={"id": user_id}, limit=1)
        if users:
            current_days = users[0].get("annual_leave_days", 12)
            new_days = max(0, current_days - days)
            db.update(
                "users",
                {"annual_leave_days": new_days},
                filters={"id": user_id},
            )

    return leave


def reject_leave(leave_id: int, approved_by_id: int) -> dict | None:
    """Từ chối đơn nghỉ.

    Args:
        leave_id: ID đơn nghỉ.
        approved_by_id: ID user (admin/manager) từ chối.

    Returns:
        dict | None: Leave record đã update, hoặc None nếu không tìm thấy.
    """
    tz = get_tz()
    now = datetime.now(tz).isoformat()

    return db.update(
        "leaves",
        {
            "status": "rejected",
            "approved_by": approved_by_id,
            "processed_at": now,
        },
        filters={"id": leave_id, "status": "pending"},
    )


def get_pending_leaves() -> list[dict]:
    """Lấy danh sách đơn nghỉ đang chờ duyệt.

    Returns:
        list[dict]: Leave records có status = 'pending', mới nhất trước.
    """
    return db.select(
        "leaves",
        filters={"status": "pending"},
        order="requested_at.desc",
    )


def get_user_leaves(user_id: int, year: int | None = None) -> list[dict]:
    """Lấy lịch sử nghỉ của user.

    Args:
        user_id: ID user trong bảng users.
        year: Năm cần xem. None = tất cả.

    Returns:
        list[dict]: Leave records, mới nhất trước.
    """
    filters: dict = {"user_id": user_id}

    if year is not None:
        # Lọc theo năm dựa vào start_date
        filters["start_date.gte"] = f"{year}-01-01"
        filters["start_date.lt"] = f"{year + 1}-01-01"

    return db.select("leaves", filters=filters, order="start_date.desc")


def get_remaining_leave_days(user_id: int) -> dict:
    """Tính số ngày phép năm còn lại.

    Returns:
        dict: {
            "total": int — tổng ngày phép năm,
            "used": float — đã dùng (approved annual leaves),
            "remaining": float — còn lại,
        }
    """
    # Lấy tổng ngày phép
    users = db.select("users", filters={"id": user_id}, limit=1)
    total = users[0].get("annual_leave_days", 12) if users else 12

    # Tính số ngày đã dùng (approved annual leaves, năm hiện tại)
    tz = get_tz()
    current_year = datetime.now(tz).year

    approved_leaves = db.select(
        "leaves",
        filters={
            "user_id": user_id,
            "leave_type": "annual",
            "status": "approved",
            "start_date.gte": f"{current_year}-01-01",
            "start_date.lt": f"{current_year + 1}-01-01",
        },
    )

    used = sum(float(leave.get("days_count", 0)) for leave in approved_leaves)

    return {
        "total": total,
        "used": used,
        "remaining": max(0, total - used),
    }
