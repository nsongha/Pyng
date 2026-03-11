"""Pyng — QR Check-in Handler.

Hai entry points:
1. handle_qr_deeplink() — gọi từ start.py deep link (/start qr_TOKEN)
2. /checkin_qr command — manual input mã QR (ConversationHandler)
"""

import logging

logger = logging.getLogger(__name__)

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from bot.handlers._helpers import get_active_user_or_none, get_ontime_status, format_current_time
from services.qr_service import validate_qr_token, mark_qr_used
from services.checkin_service import create_checkin, has_checked_in_today
from services.office_service import get_active_office

# Conversation state cho /checkin_qr
ENTERING_QR_CODE = 200


async def handle_qr_deeplink(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    token: str,
) -> None:
    """Xử lý QR check-in qua deep link.

    Gọi từ start.py khi user mở /start qr_TOKEN.

    Args:
        update: Telegram update.
        context: Bot context.
        token: QR token (phần sau "qr_").
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

    # 3. Validate QR token
    qr_session = validate_qr_token(token)
    if not qr_session:
        await update.message.reply_text(
            "❌ Mã QR không hợp lệ hoặc đã hết hạn.\n"
            "Hãy quét lại mã QR mới trên màn hình.",
        )
        return

    # 4. Mark QR as used
    mark_qr_used(token)

    # 5. Tạo checkin record
    office = get_active_office()
    office_id = office["id"] if office else qr_session.get("office_id")

    checkin = create_checkin(
        user_id=user["id"],
        checkin_type="in",
        method="qr",
        office_id=office_id,
    )

    # 6. Reply success
    time_str, date_str = format_current_time()
    ontime = get_ontime_status()

    await update.message.reply_text(
        f"✅ **Check-in thành công!** (QR Code)\n\n"
        f"👤 {user['full_name']}\n"
        f"🕐 {time_str} — {date_str}\n"
        f"{ontime}\n"
        f"📍 Phương thức: QR Code\n\n"
        f"Chúc bạn ngày làm việc hiệu quả! 💪",
        parse_mode="Markdown",
    )


async def checkin_qr_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Xử lý lệnh /checkin_qr — hỏi nhập mã QR thủ công.

    Cho trường hợp Telegram Desktop không scan được QR.
    """
    user = get_active_user_or_none(update.effective_user.id)
    if not user:
        await update.message.reply_text(
            "❌ Bạn chưa đăng ký hoặc chưa được duyệt.\n"
            "Gõ /start để đăng ký.",
        )
        return ConversationHandler.END

    if has_checked_in_today(user["id"]):
        await update.message.reply_text(
            "ℹ️ Bạn đã check-in hôm nay rồi.\n"
            "Gõ /checkout khi về nhé!",
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "🔢 Nhập **mã QR** hiển thị trên màn hình (8 ký tự):\n"
        "Hoặc /cancel để hủy.",
        parse_mode="Markdown",
    )
    return ENTERING_QR_CODE


async def receive_qr_code(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Nhận mã QR từ user, validate và check-in."""
    token = update.message.text.strip().upper()

    # Validate format
    if len(token) != 8 or not token.isalnum():
        await update.message.reply_text(
            "❌ Mã QR phải là 8 ký tự chữ/số.\n"
            "Vui lòng nhập lại hoặc /cancel:",
        )
        return ENTERING_QR_CODE

    # Dùng chung logic với deep link
    await handle_qr_deeplink(update, context, token)
    return ConversationHandler.END


async def cancel_qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Hủy nhập mã QR."""
    await update.message.reply_text(
        "❌ Đã hủy. Gõ /checkin_qr để thử lại.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


def get_qr_checkin_handler() -> ConversationHandler:
    """Tạo ConversationHandler cho /checkin_qr.

    Returns:
        ConversationHandler: Handler cho manual QR code input.
    """
    return ConversationHandler(
        entry_points=[CommandHandler("checkin_qr", checkin_qr_command)],
        states={
            ENTERING_QR_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_qr_code),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_qr)],
    )
