"""Pyng — GPS Check-in Handler.

B3: GPS check-in — nhận location, validate geofence, lưu DB.
Cung cấp /checkin command + location message handler.
"""

import logging

from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from services.checkin_service import create_checkin, has_checked_in_today, get_today_checkin
from services.office_service import get_active_office
from bot.validators.gps_validator import validate_location
from bot.handlers._helpers import get_active_user_or_none, get_ontime_status, format_current_time
from config.settings import OFFICE_LAT, OFFICE_LNG, DEFAULT_GEOFENCE_RADIUS_M

logger = logging.getLogger(__name__)


async def checkin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lệnh /checkin — gửi location keyboard."""
    user = get_active_user_or_none(update.effective_user.id)
    if not user:
        await update.message.reply_text(
            "❌ Bạn chưa đăng ký hoặc chưa được duyệt.\nGõ /start để đăng ký."
        )
        return

    # Check duplicate
    if has_checked_in_today(user["id"]):
        checkin = get_today_checkin(user["id"])
        checkin_time = checkin.get("checked_at", "")[:16] if checkin else "?"
        await update.message.reply_text(
            f"ℹ️ Bạn đã check-in hôm nay lúc {checkin_time}\n\n"
            "Gõ /checkout nếu muốn check-out."
        )
        return

    # Gửi location keyboard
    location_keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("📍 Chia sẻ vị trí", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text(
        "Nhấn nút bên dưới để chia sẻ vị trí của bạn 👇\n\n"
        "Hoặc gõ /checkin_wifi để check-in bằng WiFi.",
        reply_markup=location_keyboard,
    )


async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý khi user gửi location — GPS check-in."""
    user = get_active_user_or_none(update.effective_user.id)
    if not user:
        await update.message.reply_text(
            "❌ Bạn chưa đăng ký. Gõ /start.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    # Check duplicate
    if has_checked_in_today(user["id"]):
        await update.message.reply_text(
            "ℹ️ Bạn đã check-in hôm nay rồi.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    location = update.message.location

    # Lấy office config
    office = get_active_office()
    if not office:
        # Fallback dùng config mặc định
        office_lat = OFFICE_LAT
        office_lng = OFFICE_LNG
        radius_m = DEFAULT_GEOFENCE_RADIUS_M
        office_id = None
        office_name = "Văn phòng"
    else:
        office_lat = float(office["latitude"])
        office_lng = float(office["longitude"])
        radius_m = office["radius_m"]
        office_id = office["id"]
        office_name = office["name"]

    # Validate GPS
    result = validate_location(
        lat=location.latitude,
        lng=location.longitude,
        office_lat=office_lat,
        office_lng=office_lng,
        radius_m=radius_m,
    )

    if not result.is_valid:
        await update.message.reply_text(
            f"{result.message}\n\n"
            "Thử phương thức khác?\n"
            "📶 /checkin_wifi — Check-in bằng WiFi",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    # Lưu DB
    create_checkin(
        user_id=user["id"],
        checkin_type="in",
        method="gps",
        office_id=office_id,
        latitude=location.latitude,
        longitude=location.longitude,
        distance_m=int(result.distance_m),
    )

    # Response đẹp
    time_str, date_str = format_current_time()
    status = get_ontime_status()

    await update.message.reply_text(
        f"✅ **CHECK-IN THÀNH CÔNG!**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 {user['full_name']}\n"
        f"🕐 {time_str} — {date_str}\n"
        f"📍 {office_name} (cách {result.distance_m:.0f}m)\n"
        f"{status}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Gõ /checkout khi tan làm 🚪",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )


def get_gps_checkin_handlers() -> list:
    """Trả về GPS check-in handlers.

    Returns:
        list: [CommandHandler(/checkin), MessageHandler(LOCATION)]
    """
    return [
        CommandHandler("checkin", checkin_command),
        MessageHandler(filters.LOCATION, handle_location),
    ]
