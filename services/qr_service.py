"""Pyng — QR Service.

CRUD operations cho bảng `qr_sessions`.
Business logic: tạo QR session, validate token, generate QR image.
"""

import uuid
import io
import logging
from datetime import datetime, timedelta

import qrcode
from qrcode.image.pil import PilImage

from db import client as db
from config.settings import QR_EXPIRE_SECONDS, BOT_USERNAME
from config.timezone import get_tz

logger = logging.getLogger(__name__)


def _generate_token() -> str:
    """Tạo token unique 8 ký tự uppercase.

    Returns:
        str: Token dạng "A1B2C3D4".
    """
    return uuid.uuid4().hex[:8].upper()


def _build_deep_link(token: str) -> str:
    """Tạo Telegram deep link URL từ token.

    Args:
        token: QR token.

    Returns:
        str: Deep link URL dạng https://t.me/BOT?start=qr_TOKEN
    """
    return f"https://t.me/{BOT_USERNAME}?start=qr_{token}"


def create_qr_session(office_id: int) -> dict:
    """Tạo QR session mới với token unique.

    Args:
        office_id: ID văn phòng.

    Returns:
        dict: QR session record vừa tạo.
    """
    tz = get_tz()
    now = datetime.now(tz)
    expire_at = now + timedelta(seconds=QR_EXPIRE_SECONDS)

    token = _generate_token()

    data = {
        "token": token,
        "office_id": office_id,
        "expire_at": expire_at.isoformat(),
        "is_used": False,
    }

    return db.insert("qr_sessions", data)


def validate_qr_token(token: str) -> dict | None:
    """Validate QR token: tồn tại + chưa used + chưa expired.

    Args:
        token: QR token cần validate.

    Returns:
        dict | None: QR session nếu valid, None nếu không.
    """
    tz = get_tz()
    now = datetime.now(tz)

    rows = db.select(
        "qr_sessions",
        filters={
            "token": token,
            "is_used": False,
            "expire_at.gte": now.isoformat(),
        },
        limit=1,
    )

    return rows[0] if rows else None


def mark_qr_used(token: str) -> dict | None:
    """Đánh dấu QR token đã sử dụng.

    Args:
        token: QR token.

    Returns:
        dict | None: Updated record.
    """
    return db.update(
        "qr_sessions",
        {"is_used": True},
        filters={"token": token},
    )


def get_current_qr(office_id: int) -> dict:
    """Lấy QR đang active. Tạo mới nếu không có.

    Args:
        office_id: ID văn phòng.

    Returns:
        dict: QR session record (active hoặc vừa tạo).
    """
    tz = get_tz()
    now = datetime.now(tz)

    # Tìm QR đang active (chưa used, chưa expired)
    rows = db.select(
        "qr_sessions",
        filters={
            "office_id": office_id,
            "is_used": False,
            "expire_at.gte": now.isoformat(),
        },
        order="expire_at.desc",
        limit=1,
    )

    if rows:
        return rows[0]

    # Không có → tạo mới
    return create_qr_session(office_id)


def generate_qr_image(deep_link_url: str) -> bytes:
    """Tạo QR code image dưới dạng PNG bytes.

    Args:
        deep_link_url: URL encode vào QR code.

    Returns:
        bytes: PNG image data.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(deep_link_url)
    qr.make(fit=True)

    img: PilImage = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def cleanup_expired_qr() -> list[dict]:
    """Xóa QR sessions đã expired.

    Returns:
        list[dict]: Danh sách records đã xóa.
    """
    tz = get_tz()
    now = datetime.now(tz)

    return db.delete(
        "qr_sessions",
        filters={"expire_at.lt": now.isoformat()},
    )
