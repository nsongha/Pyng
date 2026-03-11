"""Pyng — Manual Check-in Handler (Selfie Fallback).

Flow: /manual hoặc /checkin_manual
→ Hỏi lý do (text)
→ Nhận ảnh selfie (photo)
→ Gửi notification cho admin group
→ Reply "Đang chờ admin duyệt..."

Admin approve/reject logic nằm trong admin.py (section C2).
"""

import logging

logger = logging.getLogger(__name__)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from bot.handlers._helpers import get_active_user_or_none, format_current_time
from services.checkin_service import has_checked_in_today
from config.settings import ADMIN_GROUP_ID

# Conversation states
ENTERING_REASON = 300
ENTERING_PHOTO = 301


async def manual_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Bắt đầu manual check-in flow.

    Entry points: /manual hoặc /checkin_manual.
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

    # Lưu user info cho các bước sau
    context.user_data["manual_user"] = user

    await update.message.reply_text(
        "📸 **Check-in thủ công (Manual Fallback)**\n\n"
        "Phương thức này cần admin duyệt.\n"
        "Vui lòng cho biết **lý do** không thể check-in bằng cách khác:\n\n"
        "_Ví dụ: Hết pin, WiFi lỗi, không quét được QR..._\n\n"
        "Hoặc /cancel để hủy.",
        parse_mode="Markdown",
    )
    return ENTERING_REASON


async def receive_reason(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Nhận lý do, hỏi ảnh selfie."""
    reason = update.message.text.strip()

    if len(reason) < 3:
        await update.message.reply_text(
            "❌ Lý do quá ngắn. Vui lòng nhập chi tiết hơn:",
        )
        return ENTERING_REASON

    if len(reason) > 500:
        await update.message.reply_text(
            "❌ Lý do quá dài (tối đa 500 ký tự). Vui lòng rút gọn:",
        )
        return ENTERING_REASON

    context.user_data["manual_reason"] = reason

    await update.message.reply_text(
        "📷 Gửi **ảnh selfie** tại nơi làm việc:\n\n"
        "_Chụp ảnh trực tiếp (không gửi file). "
        "Ảnh tối đa 20MB._\n\n"
        "Hoặc /cancel để hủy.",
        parse_mode="Markdown",
    )
    return ENTERING_PHOTO


async def receive_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Nhận ảnh selfie, gửi notification cho admin, trả lời user."""
    if not update.message.photo:
        await update.message.reply_text(
            "❌ Vui lòng gửi **ảnh** (không phải file/document).\n"
            "Chụp ảnh trực tiếp hoặc chọn từ gallery:",
            parse_mode="Markdown",
        )
        return ENTERING_PHOTO

    # Lấy ảnh resolution cao nhất
    photo = update.message.photo[-1]
    photo_file_id = photo.file_id

    # Validate file size (Telegram limit 20MB, nhưng warn > 10MB)
    if photo.file_size and photo.file_size > 20 * 1024 * 1024:
        await update.message.reply_text(
            "❌ Ảnh quá lớn (> 20MB).\n"
            "Vui lòng chụp lại bằng camera thường (không dùng pro mode).",
        )
        return ENTERING_PHOTO

    user = context.user_data.get("manual_user")
    reason = context.user_data.get("manual_reason", "")
    telegram_id = update.effective_user.id
    time_str, date_str = format_current_time()

    # Lưu pending data vào bot_data (để admin callback handler dùng)
    pending_key = f"manual_pending_{telegram_id}"
    context.bot_data[pending_key] = {
        "user": user,
        "telegram_id": telegram_id,
        "reason": reason,
        "photo_file_id": photo_file_id,
        "time_str": time_str,
        "date_str": date_str,
    }

    # Gửi notification cho admin group
    admin_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Duyệt", callback_data=f"manual_approve_{telegram_id}"),
            InlineKeyboardButton("❌ Từ chối", callback_data=f"manual_reject_{telegram_id}"),
        ],
    ])

    admin_text = (
        f"📸 **Yêu cầu check-in thủ công**\n\n"
        f"👤 {user['full_name']}"
    )
    if update.effective_user.username:
        admin_text += f" (@{update.effective_user.username})"
    admin_text += (
        f"\n🕐 {time_str} — {date_str}\n"
        f"📝 Lý do: _{reason}_\n\n"
        f"Duyệt hoặc từ chối:"
    )

    try:
        if ADMIN_GROUP_ID:
            # Gửi ảnh kèm caption vào admin group
            await context.bot.send_photo(
                chat_id=ADMIN_GROUP_ID,
                photo=photo_file_id,
                caption=admin_text,
                parse_mode="Markdown",
                reply_markup=admin_keyboard,
            )
        else:
            logger.warning("ADMIN_GROUP_ID not configured, cannot send manual checkin notification")
    except Exception as e:
        logger.error("Failed to send manual checkin notification to admin: %s", e)

    # Reply user
    await update.message.reply_text(
        "⏳ **Đang chờ admin duyệt...**\n\n"
        "Yêu cầu check-in thủ công của bạn đã được gửi.\n"
        "Bạn sẽ nhận thông báo khi admin xử lý.\n\n"
        f"📝 Lý do: _{reason}_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )

    # Cleanup user_data
    context.user_data.pop("manual_user", None)
    context.user_data.pop("manual_reason", None)

    return ConversationHandler.END


async def cancel_manual(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Hủy manual check-in flow."""
    context.user_data.pop("manual_user", None)
    context.user_data.pop("manual_reason", None)

    await update.message.reply_text(
        "❌ Đã hủy. Gõ /manual để thử lại.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


def get_manual_checkin_handler() -> ConversationHandler:
    """Tạo ConversationHandler cho manual check-in.

    Entry points: /manual, /checkin_manual.
    Flow: command → lý do (text) → ảnh (photo) → pending.

    Returns:
        ConversationHandler: Handler cho manual fallback.
    """
    return ConversationHandler(
        entry_points=[
            CommandHandler("manual", manual_command),
            CommandHandler("checkin_manual", manual_command),
        ],
        states={
            ENTERING_REASON: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_reason),
            ],
            ENTERING_PHOTO: [
                MessageHandler(filters.PHOTO, receive_photo),
                # Bắt text/document để thông báo cần gửi ảnh
                MessageHandler(
                    (filters.TEXT | filters.Document.ALL) & ~filters.COMMAND,
                    _not_a_photo,
                ),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_manual)],
    )


async def _not_a_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Thông báo khi user gửi text/document thay vì ảnh."""
    await update.message.reply_text(
        "❌ Vui lòng gửi **ảnh** (không phải text hoặc file).\n"
        "Chụp ảnh trực tiếp hoặc chọn từ gallery:",
        parse_mode="Markdown",
    )
    return ENTERING_PHOTO
