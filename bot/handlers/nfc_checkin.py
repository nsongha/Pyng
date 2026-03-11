"""Pyng — NFC Check-in Handler.

Entry point duy nhất: handle_nfc_deeplink()
Gọi từ start.py deep link (/start nfc_TOKEN).

NFC khác QR: chỉ có deep link (chạm tag → mở URL),
không có manual input command.
"""

import logging

logger = logging.getLogger(__name__)

from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers._helpers import get_active_user_or_none, get_ontime_status, format_current_time
from services.nfc_service import validate_nfc_token
from services.checkin_service import create_checkin, has_checked_in_today
from services.office_service import get_active_office


async def handle_nfc_deeplink(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    token: str,
) -> None:
    """Xử lý NFC check-in qua deep link.

    Gọi từ start.py khi user mở /start nfc_TOKEN.

    Args:
        update: Telegram update.
        context: Bot context.
        token: NFC token (phần sau "nfc_").
    """
    telegram_id = update.effective_user.id

    # 1. Check user đã đăng ký + active
    user = get_active_user_or_none(telegram_id)
    if not user:
        await update.message.reply_text(
            "❌ Bạn chưa đăng ký hoặc chưa được duyệt.\n"
            "Gõ /start để đăng ký.",
        )
        return

    # 2. Check đã check-in hôm nay chưa
    if has_checked_in_today(user["id"]):
        await update.message.reply_text(
            "ℹ️ Bạn đã check-in hôm nay rồi.\n"
            "Gõ /checkout khi về nhé!",
        )
        return

    # 3. Validate NFC token
    nfc_token = validate_nfc_token(token)
    if not nfc_token:
        await update.message.reply_text(
            "❌ NFC tag không hợp lệ hoặc đã bị vô hiệu hóa.\n"
            "Liên hệ admin nếu cần hỗ trợ.",
        )
        return

    # 4. Tạo checkin record
    office = get_active_office()
    office_id = office["id"] if office else nfc_token.get("office_id")

    checkin = create_checkin(
        user_id=user["id"],
        checkin_type="in",
        method="nfc",
        office_id=office_id,
    )

    # 5. Reply success
    time_str, date_str = format_current_time()
    ontime = get_ontime_status()

    location_text = nfc_token.get("location", "")
    location_line = f"📌 Vị trí: {location_text}\n" if location_text else ""

    await update.message.reply_text(
        f"✅ **Check-in thành công!** (NFC Tag)\n\n"
        f"👤 {user['full_name']}\n"
        f"🕐 {time_str} — {date_str}\n"
        f"{ontime}\n"
        f"📍 Phương thức: NFC Tag\n"
        f"{location_line}\n"
        f"Chúc bạn ngày làm việc hiệu quả! 💪",
        parse_mode="Markdown",
    )
