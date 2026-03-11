"""Pyng — WiFi Check-in Handler.

B4: WiFi check-in — nhập SSID, validate whitelist, lưu DB.
"""

import logging

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from services.checkin_service import create_checkin, has_checked_in_today
from services.office_service import get_active_office, get_wifi_whitelist
from bot.validators.wifi_validator import validate_wifi
from bot.handlers._helpers import get_active_user_or_none, get_ontime_status, format_current_time, handle_post_checkin

logger = logging.getLogger(__name__)

# Conversation state
WIFI_SSID_INPUT = 200


async def checkin_wifi_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Lệnh /checkin_wifi — hỏi SSID."""
    user = get_active_user_or_none(update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ Bạn chưa đăng ký. Gõ /start.")
        return ConversationHandler.END

    if has_checked_in_today(user["id"]):
        await update.message.reply_text("ℹ️ Bạn đã check-in hôm nay rồi.")
        return ConversationHandler.END

    await update.message.reply_text(
        "📶 Nhập tên mạng WiFi bạn đang kết nối:\n"
        "(Vào Settings > WiFi để xem tên mạng)\n\n"
        "Hoặc /cancel để hủy."
    )
    return WIFI_SSID_INPUT


async def handle_wifi_ssid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Nhận SSID, validate, tạo check-in."""
    user = get_active_user_or_none(update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ Bạn chưa đăng ký. Gõ /start.")
        return ConversationHandler.END

    ssid = update.message.text.strip()
    whitelist = get_wifi_whitelist()

    result = validate_wifi(ssid, whitelist)

    if not result.is_valid:
        await update.message.reply_text(
            f"{result.message}\n\n"
            "Bạn đang kết nối đúng mạng chưa?\n"
            "🔄 Nhập lại hoặc /cancel để hủy."
        )
        return WIFI_SSID_INPUT

    # Lấy office
    office = get_active_office()
    office_id = office["id"] if office else None

    # Lưu DB
    checkin = create_checkin(
        user_id=user["id"],
        checkin_type="in",
        method="wifi",
        office_id=office_id,
        wifi_ssid=result.matched_ssid,
    )

    # Gamification + mood (Phase 4)
    gami_text = await handle_post_checkin(
        user_id=user["id"],
        checkin_id=checkin.get("id", 0),
        checkin_type="in",
        chat_id=update.effective_chat.id,
        context=context,
    )

    # Response
    time_str, date_str = format_current_time()
    status = get_ontime_status()
    gami_line = f"\n{gami_text}" if gami_text else ""

    await update.message.reply_text(
        f"✅ **CHECK-IN THÀNH CÔNG!**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 {user['full_name']}\n"
        f"🕐 {time_str} — {date_str}\n"
        f"📶 WiFi: {result.matched_ssid} ✓\n"
        f"{status}{gami_line}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Gõ /checkout khi tan làm 🚪",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def wifi_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Hủy WiFi check-in."""
    await update.message.reply_text("❌ Đã hủy.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def get_wifi_checkin_handler() -> ConversationHandler:
    """Tạo ConversationHandler cho WiFi check-in.

    Returns:
        ConversationHandler: /checkin_wifi handler.
    """
    return ConversationHandler(
        entry_points=[CommandHandler("checkin_wifi", checkin_wifi_command)],
        states={
            WIFI_SSID_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wifi_ssid),
            ],
        },
        fallbacks=[CommandHandler("cancel", wifi_cancel)],
    )
