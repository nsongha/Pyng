"""Pyng — Checkout Handler.

B5: Check-out — tính working hours.
"""

import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from services.checkin_service import has_checked_in_today, get_today_checkin, create_checkout
from bot.handlers._helpers import get_active_user_or_none, format_current_time, handle_post_checkin

logger = logging.getLogger(__name__)


async def checkout_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lệnh /checkout — check-out và tính working hours."""
    user = get_active_user_or_none(update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ Bạn chưa đăng ký. Gõ /start.")
        return

    if not has_checked_in_today(user["id"]):
        await update.message.reply_text(
            "❌ Bạn chưa check-in hôm nay.\nGõ /checkin để check-in trước."
        )
        return

    # Check đã checkout chưa
    existing_checkout = get_today_checkin(user["id"], "out")
    if existing_checkout:
        await update.message.reply_text("ℹ️ Bạn đã check-out hôm nay rồi.")
        return

    result = create_checkout(user["id"])

    if "error" in result:
        await update.message.reply_text(f"❌ {result['error']}")
        return

    # Gamification cho checkout (Phase 4)
    checkout = result.get("checkout", {})
    gami_text = await handle_post_checkin(
        user_id=user["id"],
        checkin_id=checkout.get("id", 0),
        checkin_type="out",
        chat_id=update.effective_chat.id,
        context=context,
    )

    time_str, _ = format_current_time()
    hours = result["working_hours"]
    minutes = result["working_minutes"]
    hours_display = f"{int(hours)} giờ {minutes % 60} phút"
    gami_line = f"\n{gami_text}" if gami_text else ""

    await update.message.reply_text(
        f"✅ **CHECK-OUT THÀNH CÔNG!**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 Ra về: {time_str}\n"
        f"⏱️ Thời gian làm việc: {hours_display}{gami_line}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Nghỉ ngơi ngon nhé! 🌙",
        parse_mode="Markdown",
    )


def get_checkout_handler() -> CommandHandler:
    """Trả về checkout command handler.

    Returns:
        CommandHandler: /checkout handler.
    """
    return CommandHandler("checkout", checkout_command)
