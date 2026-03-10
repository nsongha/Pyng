"""Pyng — Handler /start — Registration flow.

ConversationHandler với states:
1. ENTERING_NAME: Hỏi họ tên
2. ENTERING_EMAIL: Hỏi email
3. Lưu DB pending → gửi notification cho admin
"""

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from services.user_service import register_user, get_by_telegram_id
from config.settings import ADMIN_GROUP_ID

# Conversation states
ENTERING_NAME, ENTERING_EMAIL = range(2)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Xử lý lệnh /start.

    Nếu user đã đăng ký → welcome back.
    Nếu chưa → bắt đầu registration flow.
    """
    user = update.effective_user
    existing = get_by_telegram_id(user.id)

    if existing:
        if existing.get("is_active"):
            await update.message.reply_text(
                f"👋 Chào mừng trở lại, **{existing['full_name']}**\\!\n\n"
                f"Bạn đã đăng ký và được duyệt\\.\n"
                f"Gõ /checkin để check\\-in ngay\\.",
                parse_mode="MarkdownV2",
            )
        else:
            await update.message.reply_text(
                "⏳ Tài khoản của bạn đang chờ admin duyệt.\n"
                "Bạn sẽ nhận thông báo khi được xử lý.",
            )
        return ConversationHandler.END

    # Bắt đầu registration
    await update.message.reply_text(
        f"👋 Xin chào **{user.first_name}**!\n\n"
        "Tôi là **PyngBot** — trợ lý chấm công BSMlabs.\n"
        '_"Ping your presence"_ 📍\n\n'
        "Để bắt đầu, bạn cần đăng ký tài khoản.\n"
        "Vui lòng nhập **họ tên đầy đủ** của bạn:",
        parse_mode="Markdown",
    )
    return ENTERING_NAME


async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Nhận họ tên, hỏi email."""
    full_name = update.message.text.strip()

    if len(full_name) < 2:
        await update.message.reply_text("❌ Tên quá ngắn. Vui lòng nhập lại họ tên đầy đủ:")
        return ENTERING_NAME

    if len(full_name) > 200:
        await update.message.reply_text("❌ Tên quá dài. Vui lòng nhập lại:")
        return ENTERING_NAME

    context.user_data["full_name"] = full_name
    await update.message.reply_text(
        f"Xin chào **{full_name}**! 👋\n\n"
        "Nhập **email công ty** của bạn:",
        parse_mode="Markdown",
    )
    return ENTERING_EMAIL


async def enter_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Nhận email, lưu DB, gửi notification cho admin."""
    email = update.message.text.strip().lower()

    # Validate email đơn giản
    if "@" not in email or "." not in email:
        await update.message.reply_text("❌ Email không hợp lệ. Vui lòng nhập lại:")
        return ENTERING_EMAIL

    user = update.effective_user
    full_name = context.user_data.get("full_name", user.first_name)

    try:
        new_user = register_user(
            telegram_id=user.id,
            telegram_username=user.username,
            full_name=full_name,
            email=email,
        )
    except Exception as e:
        error_msg = str(e)
        if "duplicate" in error_msg.lower() or "unique" in error_msg.lower():
            await update.message.reply_text(
                "❌ Email hoặc Telegram ID đã được đăng ký.\n"
                "Liên hệ admin nếu cần hỗ trợ.",
            )
        else:
            await update.message.reply_text(
                "❌ Có lỗi xảy ra. Vui lòng thử lại sau.",
            )
            print(f"[Registration Error] {e}")
        return ConversationHandler.END

    # Thông báo cho user
    await update.message.reply_text(
        "✅ Đăng ký thành công!\n\n"
        f"Chào mừng **{full_name}** 🎉\n\n"
        "Tài khoản đang chờ Admin xác nhận.\n"
        "Bạn sẽ nhận thông báo khi được duyệt.",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )

    # Gửi notification cho admin group
    if ADMIN_GROUP_ID:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Duyệt", callback_data=f"approve_{user.id}"),
                InlineKeyboardButton("❌ Từ chối", callback_data=f"reject_{user.id}"),
            ]
        ])

        username_text = f"@{user.username}" if user.username else "Không có"
        await context.bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            text=(
                "🆕 **Nhân viên mới đăng ký:**\n\n"
                f"👤 Tên: {full_name}\n"
                f"📧 Email: {email}\n"
                f"💬 Telegram: {username_text}\n"
                f"🆔 ID: `{user.id}`"
            ),
            parse_mode="Markdown",
            reply_markup=keyboard,
        )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Hủy registration flow."""
    await update.message.reply_text(
        "❌ Đã hủy đăng ký. Gõ /start để bắt đầu lại.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


def get_registration_handler() -> ConversationHandler:
    """Tạo ConversationHandler cho registration flow.

    Returns:
        ConversationHandler: Handler cho /start registration.
    """
    return ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            ENTERING_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name),
            ],
            ENTERING_EMAIL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_email),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
