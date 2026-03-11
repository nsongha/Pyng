"""Pyng — NFC Service.

CRUD operations cho bảng `nfc_tokens`.
Business logic: tạo NFC token, validate, list, deactivate.

Khác với QR: NFC token KHÔNG expire (cố định trên tag vật lý),
chỉ dùng `is_active` để quản lý.
"""

import uuid
import logging

from db import client as db
from config.settings import BOT_USERNAME

logger = logging.getLogger(__name__)


def _generate_nfc_token() -> str:
    """Tạo token unique 12 ký tự uppercase.

    Dài hơn QR (8 chars) vì NFC token cố định lâu dài, cần unique hơn.

    Returns:
        str: Token dạng "A1B2C3D4E5F6".
    """
    return uuid.uuid4().hex[:12].upper()


def build_nfc_deep_link(token: str) -> str:
    """Tạo Telegram deep link URL từ NFC token.

    URL này sẽ được ghi vào NFC tag.

    Args:
        token: NFC token.

    Returns:
        str: Deep link URL dạng https://t.me/BOT?start=nfc_TOKEN
    """
    return f"https://t.me/{BOT_USERNAME}?start=nfc_{token}"


def create_nfc_token(office_id: int, location: str = "") -> dict:
    """Tạo NFC token mới.

    Args:
        office_id: ID văn phòng.
        location: Mô tả vị trí đặt tag (vd "Cửa chính tầng 1").

    Returns:
        dict: NFC token record vừa tạo.
    """
    token = _generate_nfc_token()

    data = {
        "token": token,
        "office_id": office_id,
        "location": location,
        "is_active": True,
    }

    return db.insert("nfc_tokens", data)


def validate_nfc_token(token: str) -> dict | None:
    """Validate NFC token: tồn tại + is_active.

    Args:
        token: NFC token cần validate.

    Returns:
        dict | None: NFC token record nếu valid, None nếu không.
    """
    rows = db.select(
        "nfc_tokens",
        filters={
            "token": token,
            "is_active": True,
        },
        limit=1,
    )

    return rows[0] if rows else None


def list_nfc_tokens(office_id: int | None = None) -> list[dict]:
    """Lấy danh sách NFC tokens.

    Args:
        office_id: Lọc theo văn phòng. None = lấy tất cả.

    Returns:
        list[dict]: Danh sách NFC token records.
    """
    filters = {}
    if office_id is not None:
        filters["office_id"] = office_id

    return db.select(
        "nfc_tokens",
        filters=filters if filters else None,
        order="created_at.desc",
    )


def deactivate_nfc_token(token_id: int) -> dict | None:
    """Vô hiệu hóa NFC token.

    Args:
        token_id: ID của NFC token record.

    Returns:
        dict | None: Updated record, hoặc None nếu không tìm thấy.
    """
    return db.update(
        "nfc_tokens",
        {"is_active": False},
        filters={"id": token_id},
    )
