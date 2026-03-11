"""Pyng — WFH Handler.

B6: WFH — đăng ký Work From Home, check limit 2 lần/tháng.
"""

import logging
from datetime import datetime

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from services.checkin_service import has_checked_in_today, create_wfh_checkin
from bot.handlers._helpers import get_active_user_or_none, handle_post_checkin
from config.timezone import get_tz

logger = logging.getLogger(__name__)

# Conversation state
WFH_NOTE_INPUT = 201


async def wfh_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Lệnh /wfh — đăng ký Work From Home."""
    user = get_active_user_or_none(update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ Bạn chưa đăng ký. Gõ /start.")
        return ConversationHandler.END

    if has_checked_in_today(user["id"]):
        await update.message.reply_text("ℹ️ Bạn đã check-in hôm nay rồi.")
        return ConversationHandler.END

    await update.message.reply_text(
        "🏠 **Work From Home**\n\n"
        "Nhập ghi chú (lý do WFH), hoặc gõ `skip` để bỏ qua:",
        parse_mode="Markdown",
    )
    return WFH_NOTE_INPUT


async def handle_wfh_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Nhận ghi chú WFH, tạo checkin."""
    user = get_active_user_or_none(update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ Lỗi. Gõ /start.")
        return ConversationHandler.END

    text = update.message.text.strip()
    note = None if text.lower() == "skip" else text

    result = create_wfh_checkin(user["id"], note=note)

    if "error" in result:
        await update.message.reply_text(
            f"❌ {result['error']}\n"
            f"(Đã dùng {result.get('wfh_count', '?')}/{result.get('wfh_limit', '?')} lần)"
        )
        return ConversationHandler.END

    # Gamification (Phase 4) — WFH không hỏi mood
    checkin = result.get("checkin", {})
    gami_text = await handle_post_checkin(
        user_id=user["id"],
        checkin_id=checkin.get("id", 0),
        checkin_type="in",
        chat_id=update.effective_chat.id,
        context=context,
        is_wfh=True,
    )

    now = datetime.now(get_tz())
    date_str = now.strftime("%d/%m/%Y")
    gami_line = f"\n{gami_text}" if gami_text else ""

    await update.message.reply_text(
        f"✅ **Đã ghi nhận WFH!**\n\n"
        f"📅 {date_str} — Work From Home\n"
        f"📝 {note or '(không có ghi chú)'}\n"
        f"📊 WFH tháng này: {result['wfh_count']}/{result['wfh_limit']}{gami_line}\n\n"
        f"Check-out khi kết thúc ngày làm việc nhé.\n"
        f"Gõ /checkout 🚪",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def wfh_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Hủy WFH flow."""
    await update.message.reply_text("❌ Đã hủy.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def get_wfh_handler() -> ConversationHandler:
    """Tạo ConversationHandler cho WFH flow.

    Returns:
        ConversationHandler: /wfh handler.
    """
    return ConversationHandler(
        entry_points=[CommandHandler("wfh", wfh_command)],
        states={
            WFH_NOTE_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wfh_note),
            ],
        },
        fallbacks=[CommandHandler("cancel", wfh_cancel)],
    )
