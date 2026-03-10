"""Pyng — Shared helpers cho bot handlers.

Các utility functions dùng chung giữa các check-in handlers.
"""

import logging
from datetime import datetime

from services.user_service import get_by_telegram_id
from config.settings import WORK_START
from config.timezone import get_tz

logger = logging.getLogger(__name__)


def get_active_user_or_none(telegram_id: int) -> dict | None:
    """Lấy active user, trả None nếu chưa đăng ký hoặc pending.

    Args:
        telegram_id: Telegram user ID.

    Returns:
        dict | None: User record nếu active, None nếu không.
    """
    user = get_by_telegram_id(telegram_id)
    if not user or not user.get("is_active"):
        return None
    return user


def get_ontime_status() -> str:
    """Kiểm tra hiện tại đúng giờ hay muộn.

    So sánh thời gian hiện tại với WORK_START + 5 phút grace.

    Returns:
        str: "🔰 Đúng giờ" hoặc "⏰ Đi muộn".
    """
    now = datetime.now(get_tz())
    work_start_parts = WORK_START.split(":")
    work_start_minutes = int(work_start_parts[0]) * 60 + int(work_start_parts[1])
    current_minutes = now.hour * 60 + now.minute
    return "🔰 Đúng giờ" if current_minutes <= work_start_minutes + 5 else "⏰ Đi muộn"


def format_current_time() -> tuple[str, str]:
    """Lấy thời gian hiện tại đã format.

    Returns:
        tuple: (time_str "HH:MM", date_str "Weekday, DD/MM/YYYY").
    """
    now = datetime.now(get_tz())
    return now.strftime("%H:%M"), now.strftime("%A, %d/%m/%Y")
