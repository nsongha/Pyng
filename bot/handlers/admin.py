"""Pyng — Admin Handlers.

B2: Approval flow — inline buttons (Duyệt / Từ chối).
B7: Admin GPS settings — set geofence radius.
B8: Admin WiFi whitelist management — thêm/xóa SSID.
"""

import logging

logger = logging.getLogger(__name__)

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from services.user_service import activate_user, reject_user, is_admin
from services.office_service import (
    get_active_office,
    update_geofence_radius,
    get_wifi_whitelist,
    add_wifi_ssid,
    remove_wifi_ssid,
)

# Conversation states cho admin flows
ADMIN_GPS_RADIUS = 100
ADMIN_WIFI_ACTION, ADMIN_WIFI_SSID = 101, 102


# ============================================================
# B2: Approval flow
# ============================================================


async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý khi admin bấm nút Duyệt."""
    query = update.callback_query

    if not is_admin(query.from_user.id):
        await query.answer("⛔ Bạn không có quyền admin.", show_alert=True)
        return

    await query.answer()

    # Parse telegram_id từ callback_data: "approve_123456789"
    telegram_id = int(query.data.split("_")[1])

    result = activate_user(telegram_id)
    if result:
        # Cập nhật message admin
        await query.edit_message_text(
            text=query.message.text + f"\n\n✅ **Đã duyệt** bởi @{query.from_user.username}",
            parse_mode="Markdown",
        )

        # Thông báo cho user
        try:
            await context.bot.send_message(
                chat_id=telegram_id,
                text=(
                    "🎊 **Tài khoản đã được duyệt!**\n\n"
                    "Bạn có thể check-in ngay hôm nay.\n"
                    "Gõ /checkin để bắt đầu."
                ),
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.warning("Cannot notify user %s: %s", telegram_id, e)
    else:
        await query.edit_message_text(
            text=query.message.text + "\n\n❌ Lỗi: Không tìm thấy user.",
        )


async def handle_rejection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý khi admin bấm nút Từ chối."""
    query = update.callback_query

    if not is_admin(query.from_user.id):
        await query.answer("⛔ Bạn không có quyền admin.", show_alert=True)
        return

    await query.answer()

    telegram_id = int(query.data.split("_")[1])

    reject_user(telegram_id)

    # Cập nhật message admin
    await query.edit_message_text(
        text=query.message.text + f"\n\n❌ **Đã từ chối** bởi @{query.from_user.username}",
        parse_mode="Markdown",
    )

    # Thông báo cho user
    try:
        await context.bot.send_message(
            chat_id=telegram_id,
            text=(
                "❌ Yêu cầu đăng ký của bạn đã bị từ chối.\n"
                "Liên hệ admin nếu cần hỗ trợ."
            ),
        )
    except Exception as e:
        logger.warning("Cannot notify user %s: %s", telegram_id, e)


# ============================================================
# B7: Admin GPS settings
# ============================================================


async def admin_gps_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Hiển thị cài đặt GPS hiện tại, hỏi radius mới."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Bạn không có quyền admin.")
        return ConversationHandler.END

    office = get_active_office()
    if not office:
        await update.message.reply_text(
            "❌ Chưa có văn phòng nào được cấu hình.\n"
            "Vui lòng tạo office trong Supabase Dashboard trước."
        )
        return ConversationHandler.END

    context.user_data["admin_office_id"] = office["id"]

    await update.message.reply_text(
        f"🏢 **Cài đặt GPS — {office['name']}**\n\n"
        f"📍 Tọa độ: {office['latitude']}, {office['longitude']}\n"
        f"📏 Bán kính hiện tại: **{office['radius_m']}m**\n\n"
        f"Nhập bán kính mới (mét), hoặc /cancel để hủy:",
        parse_mode="Markdown",
    )
    return ADMIN_GPS_RADIUS


async def admin_gps_set_radius(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Nhận radius mới, cập nhật DB."""
    try:
        radius = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Vui lòng nhập số nguyên (mét):")
        return ADMIN_GPS_RADIUS

    if radius < 10 or radius > 5000:
        await update.message.reply_text("❌ Bán kính phải từ 10m đến 5000m:")
        return ADMIN_GPS_RADIUS

    office_id = context.user_data.get("admin_office_id")
    result = update_geofence_radius(office_id, radius)

    if result:
        await update.message.reply_text(
            f"✅ Đã cập nhật bán kính geofence: **{radius}m**",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text("❌ Lỗi cập nhật. Thử lại sau.")

    return ConversationHandler.END


# ============================================================
# B8: Admin WiFi whitelist management
# ============================================================


async def admin_wifi_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Hiển thị danh sách WiFi whitelist, chọn action."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Bạn không có quyền admin.")
        return ConversationHandler.END

    whitelist = get_wifi_whitelist()
    ssid_list = "\n".join(
        f"  {i+1}. {w['ssid']} (ID: {w['id']})"
        for i, w in enumerate(whitelist)
    ) if whitelist else "  (trống)"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Thêm SSID", callback_data="wifi_add"),
            InlineKeyboardButton("🗑️ Xóa SSID", callback_data="wifi_remove"),
        ],
        [InlineKeyboardButton("❌ Đóng", callback_data="wifi_close")],
    ])

    await update.message.reply_text(
        f"📶 **WiFi Whitelist:**\n\n{ssid_list}\n\n"
        "Chọn hành động:",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
    return ADMIN_WIFI_ACTION


async def admin_wifi_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Xử lý action từ inline buttons."""
    query = update.callback_query
    await query.answer()

    if query.data == "wifi_close":
        await query.edit_message_text("👋 Đã đóng quản lý WiFi.")
        return ConversationHandler.END

    if query.data == "wifi_add":
        context.user_data["wifi_action"] = "add"
        await query.edit_message_text(
            "📶 Nhập tên WiFi (SSID) muốn thêm:\n"
            "Hoặc /cancel để hủy."
        )
        return ADMIN_WIFI_SSID

    if query.data == "wifi_remove":
        context.user_data["wifi_action"] = "remove"
        await query.edit_message_text(
            "📶 Nhập **ID** của SSID muốn xóa:\n"
            "Hoặc /cancel để hủy.",
            parse_mode="Markdown",
        )
        return ADMIN_WIFI_SSID

    return ConversationHandler.END


async def admin_wifi_ssid_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Nhận SSID input, thực hiện add/remove."""
    action = context.user_data.get("wifi_action")
    text = update.message.text.strip()

    if action == "add":
        office = get_active_office()
        if not office:
            await update.message.reply_text("❌ Chưa có office. Tạo trong Dashboard trước.")
            return ConversationHandler.END

        result = add_wifi_ssid(
            office_id=office["id"],
            ssid=text,
            added_by=update.effective_user.id,
        )
        if result:
            await update.message.reply_text(f'✅ Đã thêm WiFi SSID: **"{text}"**', parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Lỗi thêm SSID.")

    elif action == "remove":
        try:
            ssid_id = int(text)
        except ValueError:
            await update.message.reply_text("❌ Vui lòng nhập ID số nguyên:")
            return ADMIN_WIFI_SSID

        success = remove_wifi_ssid(ssid_id)
        if success:
            await update.message.reply_text(f"✅ Đã xóa SSID ID: {ssid_id}")
        else:
            await update.message.reply_text(f"❌ Không tìm thấy SSID ID: {ssid_id}")

    return ConversationHandler.END


async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Hủy admin flow."""
    await update.message.reply_text("❌ Đã hủy.")
    return ConversationHandler.END


# ============================================================
# Handler factories
# ============================================================


def get_approval_handlers() -> list:
    """Trả về list handlers cho approval flow.

    Returns:
        list: [CallbackQueryHandler approve, CallbackQueryHandler reject]
    """
    return [
        CallbackQueryHandler(handle_approval, pattern=r"^approve_\d+$"),
        CallbackQueryHandler(handle_rejection, pattern=r"^reject_\d+$"),
    ]


def get_admin_gps_handler() -> ConversationHandler:
    """Tạo ConversationHandler cho GPS settings.

    Returns:
        ConversationHandler: /admin_gps handler.
    """
    return ConversationHandler(
        entry_points=[CommandHandler("admin_gps", admin_gps_command)],
        states={
            ADMIN_GPS_RADIUS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_gps_set_radius),
            ],
        },
        fallbacks=[CommandHandler("cancel", admin_cancel)],
    )


def get_admin_wifi_handler() -> ConversationHandler:
    """Tạo ConversationHandler cho WiFi management.

    Returns:
        ConversationHandler: /admin_wifi handler.
    """
    return ConversationHandler(
        entry_points=[CommandHandler("admin_wifi", admin_wifi_command)],
        states={
            ADMIN_WIFI_ACTION: [
                CallbackQueryHandler(admin_wifi_action, pattern=r"^wifi_"),
            ],
            ADMIN_WIFI_SSID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_wifi_ssid_input),
            ],
        },
        fallbacks=[CommandHandler("cancel", admin_cancel)],
    )
