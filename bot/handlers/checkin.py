"""Pyng — Check-in Handlers.

B3: GPS check-in — nhận location, validate geofence, lưu DB.
B4: WiFi check-in — nhập SSID, validate whitelist, lưu DB.
B5: Check-out — tính working hours.
B6: WFH — đăng ký WFH, check limit 2 lần/tháng.
"""

from datetime import datetime

from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from services.user_service import get_by_telegram_id
from services.checkin_service import (
    create_checkin,
    has_checked_in_today,
    get_today_checkin,
    create_checkout,
    create_wfh_checkin,
)
from services.office_service import get_active_office, get_wifi_whitelist
from bot.validators.gps_validator import validate_location
from bot.validators.wifi_validator import validate_wifi
from config.settings import TIMEZONE

# Conversation states
WIFI_SSID_INPUT = 200
WFH_NOTE_INPUT = 201

# Lazy timezone
_tz = None


def _get_tz():
    global _tz
    if _tz is None:
        from zoneinfo import ZoneInfo
        _tz = ZoneInfo(TIMEZONE)
    return _tz


def _get_user_or_none(telegram_id: int) -> dict | None:
    """Lấy active user, trả None nếu chưa đăng ký hoặc pending."""
    user = get_by_telegram_id(telegram_id)
    if not user or not user.get("is_active"):
        return None
    return user


# ============================================================
# B3: GPS Check-in
# ============================================================


async def checkin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lệnh /checkin — gửi location keyboard."""
    user = _get_user_or_none(update.effective_user.id)
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
    user = _get_user_or_none(update.effective_user.id)
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
        from config.settings import OFFICE_LAT, OFFICE_LNG, DEFAULT_GEOFENCE_RADIUS_M
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
    checkin_record = create_checkin(
        user_id=user["id"],
        checkin_type="in",
        method="gps",
        office_id=office_id,
        latitude=location.latitude,
        longitude=location.longitude,
        distance_m=int(result.distance_m),
    )

    # Response đẹp
    now = datetime.now(_get_tz())
    time_str = now.strftime("%H:%M")
    date_str = now.strftime("%A, %d/%m/%Y")

    # Check đúng giờ hay muộn
    from config.settings import WORK_START
    work_start_parts = WORK_START.split(":")
    work_start_minutes = int(work_start_parts[0]) * 60 + int(work_start_parts[1])
    current_minutes = now.hour * 60 + now.minute
    status = "🔰 Đúng giờ" if current_minutes <= work_start_minutes + 5 else "⏰ Đi muộn"

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


# ============================================================
# B4: WiFi Check-in
# ============================================================


async def checkin_wifi_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Lệnh /checkin_wifi — hỏi SSID."""
    user = _get_user_or_none(update.effective_user.id)
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
    user = _get_user_or_none(update.effective_user.id)
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
    create_checkin(
        user_id=user["id"],
        checkin_type="in",
        method="wifi",
        office_id=office_id,
        wifi_ssid=result.matched_ssid,
    )

    # Response
    now = datetime.now(_get_tz())
    time_str = now.strftime("%H:%M")
    date_str = now.strftime("%A, %d/%m/%Y")

    from config.settings import WORK_START
    work_start_parts = WORK_START.split(":")
    work_start_minutes = int(work_start_parts[0]) * 60 + int(work_start_parts[1])
    current_minutes = now.hour * 60 + now.minute
    status = "🔰 Đúng giờ" if current_minutes <= work_start_minutes + 5 else "⏰ Đi muộn"

    await update.message.reply_text(
        f"✅ **CHECK-IN THÀNH CÔNG!**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 {user['full_name']}\n"
        f"🕐 {time_str} — {date_str}\n"
        f"📶 WiFi: {result.matched_ssid} ✓\n"
        f"{status}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Gõ /checkout khi tan làm 🚪",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


# ============================================================
# B5: Check-out
# ============================================================


async def checkout_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lệnh /checkout — check-out và tính working hours."""
    user = _get_user_or_none(update.effective_user.id)
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

    now = datetime.now(_get_tz())
    time_str = now.strftime("%H:%M")
    hours = result["working_hours"]
    minutes = result["working_minutes"]
    hours_display = f"{int(hours)} giờ {minutes % 60} phút"

    await update.message.reply_text(
        f"✅ **CHECK-OUT THÀNH CÔNG!**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 Ra về: {time_str}\n"
        f"⏱️ Thời gian làm việc: {hours_display}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Nghỉ ngơi ngon nhé! 🌙",
        parse_mode="Markdown",
    )


# ============================================================
# B6: WFH Flow
# ============================================================


async def wfh_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Lệnh /wfh — đăng ký Work From Home."""
    user = _get_user_or_none(update.effective_user.id)
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
    user = _get_user_or_none(update.effective_user.id)
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

    now = datetime.now(_get_tz())
    date_str = now.strftime("%d/%m/%Y")

    await update.message.reply_text(
        f"✅ **Đã ghi nhận WFH!**\n\n"
        f"📅 {date_str} — Work From Home\n"
        f"📝 {note or '(không có ghi chú)'}\n"
        f"📊 WFH tháng này: {result['wfh_count']}/{result['wfh_limit']}\n\n"
        f"Check-out khi kết thúc ngày làm việc nhé.\n"
        f"Gõ /checkout 🚪",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def checkin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Hủy flow checkin."""
    await update.message.reply_text("❌ Đã hủy.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# ============================================================
# Handler factories
# ============================================================


def get_checkin_handlers() -> list:
    """Trả về list tất cả checkin-related handlers.

    Returns:
        list: [CommandHandler, MessageHandler, ConversationHandler, ...]
    """
    wifi_handler = ConversationHandler(
        entry_points=[CommandHandler("checkin_wifi", checkin_wifi_command)],
        states={
            WIFI_SSID_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wifi_ssid),
            ],
        },
        fallbacks=[CommandHandler("cancel", checkin_cancel)],
    )

    wfh_handler = ConversationHandler(
        entry_points=[CommandHandler("wfh", wfh_command)],
        states={
            WFH_NOTE_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_wfh_note),
            ],
        },
        fallbacks=[CommandHandler("cancel", checkin_cancel)],
    )

    return [
        CommandHandler("checkin", checkin_command),
        MessageHandler(filters.LOCATION, handle_location),
        wifi_handler,
        CommandHandler("checkout", checkout_command),
        wfh_handler,
    ]
