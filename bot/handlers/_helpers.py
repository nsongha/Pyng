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


# ------------------------------------------------------------------
# Phase 4: Gamification + Mood integration helpers
# ------------------------------------------------------------------


def get_checkin_timing() -> dict:
    """Tính timing check-in cho gamification.

    So sánh thời gian hiện tại với WORK_START để xác định:
    - is_early: sớm ≥15 phút trước giờ làm
    - is_ontime: trong vòng 5 phút grace
    - late_minutes: số phút đi muộn

    Returns:
        dict: {"is_ontime": bool, "is_early": bool, "late_minutes": int}
    """
    now = datetime.now(get_tz())
    work_start_parts = WORK_START.split(":")
    work_start_minutes = int(work_start_parts[0]) * 60 + int(work_start_parts[1])
    current_minutes = now.hour * 60 + now.minute

    diff = current_minutes - work_start_minutes  # negative = sớm

    is_early = diff <= -15
    is_ontime = diff <= 5
    late_minutes = max(0, diff - 5)  # muộn bao nhiêu phút so với grace

    return {
        "is_ontime": is_ontime,
        "is_early": is_early,
        "late_minutes": late_minutes,
    }


async def handle_post_checkin(
    *,
    user_id: int,
    checkin_id: int,
    checkin_type: str,
    chat_id: int,
    context,
    is_wfh: bool = False,
) -> str:
    """Xử lý gamification + mood prompt sau check-in thành công.

    Gọi hàm này sau mỗi create_checkin() thành công.
    Trả về gamification text để handler append vào response.

    Args:
        user_id: ID user (bảng users.id).
        checkin_id: ID checkin record vừa tạo.
        checkin_type: 'in' hoặc 'out'.
        chat_id: Telegram chat ID (để gửi mood prompt).
        context: Telegram bot context.
        is_wfh: True nếu WFH check-in.

    Returns:
        str: Một hoặc nhiều dòng gamification text, hoặc "" nếu không có.
    """
    from services.checkin_service import process_gamification_after_checkin
    from bot.handlers.gamification import format_gamification_line

    try:
        # 1. Tính timing
        timing = get_checkin_timing()

        # 2. Gọi gamification
        gami_result = process_gamification_after_checkin(
            user_id,
            checkin_type,
            is_ontime=timing["is_ontime"],
            is_early=timing["is_early"],
            is_wfh=is_wfh,
            late_minutes=timing["late_minutes"],
        )

        # 3. Format gamification line
        gami_text = format_gamification_line(gami_result)

        # 4. Mood prompt (chỉ khi check-in sáng, KHÔNG phải checkout/WFH)
        if checkin_type == "in" and not is_wfh:
            from bot.handlers.mood import send_mood_prompt
            await send_mood_prompt(chat_id, checkin_id, user_id, context)

        return gami_text

    except Exception:
        logger.exception("handle_post_checkin error for user_id=%s", user_id)
        return ""

