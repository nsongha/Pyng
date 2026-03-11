"""Pyng — Admin Handlers.

B2: Approval flow — inline buttons (Duyệt / Từ chối).
B7: Admin GPS settings — set geofence radius.
B8: Admin WiFi whitelist management — thêm/xóa SSID.
A8: Admin QR config — xem QR link, tạo QR mới.
B4: Admin NFC management — tạo token, xem danh sách, vô hiệu hóa.
C2: Manual check-in approval — duyệt/từ chối yêu cầu check-in thủ công.
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
from services.checkin_service import create_checkin
from services.qr_service import get_current_qr, create_qr_session, _build_deep_link
from services.nfc_service import (
    create_nfc_token,
    list_nfc_tokens,
    deactivate_nfc_token,
    build_nfc_deep_link,
)
from bot.handlers._helpers import get_ontime_status, format_current_time
from config.settings import QR_EXPIRE_SECONDS, QR_DISPLAY_URL
from db import client as db

# Conversation states cho admin flows
ADMIN_GPS_RADIUS = 100
ADMIN_WIFI_ACTION, ADMIN_WIFI_SSID = 101, 102
ADMIN_QR_ACTION = 103
ADMIN_NFC_ACTION, ADMIN_NFC_LOCATION = 106, 107
ADMIN_MANUAL_REJECT_REASON = 104


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


# ============================================================
# A8: Admin QR config
# ============================================================


async def admin_qr_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Hiển thị QR config và options."""
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

    # Lấy QR hiện tại
    qr_session = get_current_qr(office["id"])
    deep_link = _build_deep_link(qr_session["token"])

    display_url = QR_DISPLAY_URL or "(chưa cấu hình QR_DISPLAY_URL)"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Tạo QR mới", callback_data="qr_refresh"),
        ],
        [InlineKeyboardButton("❌ Đóng", callback_data="qr_close")],
    ])

    await update.message.reply_text(
        f"📱 **QR Config**\n\n"
        f"🖥️ QR Display: {display_url}\n"
        f"⏱️ Expire: {QR_EXPIRE_SECONDS}s ({QR_EXPIRE_SECONDS // 60} phút)\n\n"
        f"**QR hiện tại:**\n"
        f"🔑 Token: `{qr_session['token']}`\n"
        f"⏳ Hết hạn: {qr_session['expire_at']}\n"
        f"🔗 Deep link: {deep_link}\n\n"
        f"Chọn hành động:",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
    return ADMIN_QR_ACTION


async def admin_qr_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Xử lý action từ QR inline buttons."""
    query = update.callback_query
    await query.answer()

    if query.data == "qr_close":
        await query.edit_message_text("👋 Đã đóng QR config.")
        return ConversationHandler.END

    if query.data == "qr_refresh":
        office = get_active_office()
        if not office:
            await query.edit_message_text("❌ Không có office active.")
            return ConversationHandler.END

        qr_session = create_qr_session(office["id"])
        deep_link = _build_deep_link(qr_session["token"])

        await query.edit_message_text(
            f"✅ **QR mới đã tạo!**\n\n"
            f"🔑 Token: `{qr_session['token']}`\n"
            f"⏳ Hết hạn: {qr_session['expire_at']}\n"
            f"🔗 Deep link: {deep_link}",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    return ConversationHandler.END


def get_admin_qr_handler() -> ConversationHandler:
    """Tạo ConversationHandler cho QR config.

    Returns:
        ConversationHandler: /admin_qr handler.
    """
    return ConversationHandler(
        entry_points=[CommandHandler("admin_qr", admin_qr_command)],
        states={
            ADMIN_QR_ACTION: [
                CallbackQueryHandler(admin_qr_action, pattern=r"^qr_"),
            ],
        },
        fallbacks=[CommandHandler("cancel", admin_cancel)],
    )


# ============================================================
# C2: Admin Manual Check-in Approval
# ============================================================


async def handle_manual_approval(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Xử lý khi admin bấm nút Duyệt check-in thủ công."""
    query = update.callback_query

    if not is_admin(query.from_user.id):
        await query.answer("⛔ Bạn không có quyền admin.", show_alert=True)
        return

    await query.answer()

    # Parse telegram_id từ callback_data: "manual_approve_123456789"
    telegram_id = int(query.data.split("_")[2])
    pending_key = f"manual_pending_{telegram_id}"
    pending = context.bot_data.get(pending_key)

    if not pending:
        await query.edit_message_caption(
            caption=(query.message.caption or "") + "\n\n⚠️ Yêu cầu đã hết hạn hoặc đã xử lý.",
        )
        return

    user = pending["user"]
    reason = pending["reason"]

    # Tạo checkin record
    office = get_active_office()
    office_id = office["id"] if office else None

    checkin = create_checkin(
        user_id=user["id"],
        checkin_type="in",
        method="manual",
        office_id=office_id,
        note=reason,
    )

    # Update checkin record — set manual approval fields
    db.update(
        "checkins",
        {
            "is_manual_approved": True,
            "approved_by": query.from_user.id,
        },
        filters={"id": checkin["id"]},
    )

    # Cập nhật message admin
    await query.edit_message_caption(
        caption=(
            (query.message.caption or "")
            + f"\n\n✅ **Đã duyệt** bởi @{query.from_user.username}"
        ),
        parse_mode="Markdown",
    )

    # Thông báo cho user
    time_str = pending.get("time_str", "")
    date_str = pending.get("date_str", "")
    ontime = get_ontime_status()

    try:
        await context.bot.send_message(
            chat_id=telegram_id,
            text=(
                f"✅ **Check-in thủ công đã được duyệt!**\n\n"
                f"👤 {user['full_name']}\n"
                f"🕐 {time_str} — {date_str}\n"
                f"{ontime}\n"
                f"📍 Phương thức: Manual (Admin duyệt)\n\n"
                f"Chúc bạn ngày làm việc hiệu quả! 💪"
            ),
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.warning("Cannot notify user %s after manual approval: %s", telegram_id, e)

    # Cleanup pending data
    context.bot_data.pop(pending_key, None)


async def handle_manual_rejection(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Xử lý khi admin bấm nút Từ chối check-in thủ công."""
    query = update.callback_query

    if not is_admin(query.from_user.id):
        await query.answer("⛔ Bạn không có quyền admin.", show_alert=True)
        return

    await query.answer()

    # Parse telegram_id
    telegram_id = int(query.data.split("_")[2])
    pending_key = f"manual_pending_{telegram_id}"
    pending = context.bot_data.get(pending_key)

    if not pending:
        await query.edit_message_caption(
            caption=(query.message.caption or "") + "\n\n⚠️ Yêu cầu đã hết hạn hoặc đã xử lý.",
        )
        return

    # Cập nhật message admin
    await query.edit_message_caption(
        caption=(
            (query.message.caption or "")
            + f"\n\n❌ **Đã từ chối** bởi @{query.from_user.username}"
        ),
        parse_mode="Markdown",
    )

    # Thông báo cho user
    try:
        await context.bot.send_message(
            chat_id=telegram_id,
            text=(
                "❌ **Yêu cầu check-in thủ công bị từ chối.**\n\n"
                "Liên hệ admin nếu cần hỗ trợ.\n"
                "Hoặc thử check-in bằng phương thức khác: /checkin, /checkin_wifi, /checkin_qr"
            ),
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.warning("Cannot notify user %s after manual rejection: %s", telegram_id, e)

    # Cleanup pending data
    context.bot_data.pop(pending_key, None)


def get_manual_approval_handlers() -> list:
    """Trả về list handlers cho manual check-in approval flow.

    Returns:
        list: [CallbackQueryHandler approve, CallbackQueryHandler reject]
    """
    return [
        CallbackQueryHandler(handle_manual_approval, pattern=r"^manual_approve_\d+$"),
        CallbackQueryHandler(handle_manual_rejection, pattern=r"^manual_reject_\d+$"),
    ]


# ============================================================
# A4: Bulk approve manual check-ins (Phase 5)
# ============================================================


async def handle_bulk_approve(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Duyệt tất cả pending manual check-ins cùng lúc.

    Callback data: 'bulk_approve_all'
    """
    query = update.callback_query

    if not is_admin(query.from_user.id):
        await query.answer("⛔ Bạn không có quyền admin.", show_alert=True)
        return

    await query.answer()

    # Tìm tất cả pending manual check-ins trong bot_data
    pending_keys = [
        key for key in context.bot_data
        if key.startswith("manual_pending_")
    ]

    if not pending_keys:
        await query.edit_message_text(
            "ℹ️ Không có check-in thủ công nào đang chờ duyệt."
        )
        return

    approved_count = 0
    failed_users = []

    for pending_key in pending_keys:
        pending = context.bot_data.get(pending_key)
        if not pending:
            continue

        # Extract telegram_id từ key: "manual_pending_123456789"
        telegram_id = int(pending_key.replace("manual_pending_", ""))
        user = pending["user"]
        reason = pending.get("reason", "")

        try:
            # Tạo checkin record
            office = get_active_office()
            office_id = office["id"] if office else None

            checkin = create_checkin(
                user_id=user["id"],
                checkin_type="in",
                method="manual",
                office_id=office_id,
                note=reason,
            )

            # Update record — set manual approval fields
            db.update(
                "checkins",
                {
                    "is_manual_approved": True,
                    "approved_by": query.from_user.id,
                },
                filters={"id": checkin["id"]},
            )

            approved_count += 1

            # Notify user
            try:
                await context.bot.send_message(
                    chat_id=telegram_id,
                    text=(
                        "✅ **Check-in thủ công đã được duyệt!**\n\n"
                        f"👤 {user['full_name']}\n"
                        "📍 Phương thức: Manual (Admin bulk approve)\n\n"
                        "Chúc bạn ngày làm việc hiệu quả! 💪"
                    ),
                    parse_mode="Markdown",
                )
            except Exception as e:
                logger.warning("Cannot notify user %s after bulk approve: %s", telegram_id, e)

        except Exception as e:
            logger.exception("Bulk approve failed for user %s: %s", pending_key, e)
            failed_users.append(pending.get("user", {}).get("full_name", "Unknown"))

        # Cleanup
        context.bot_data.pop(pending_key, None)

    # Summary message
    result_text = f"✅ **Đã duyệt {approved_count} check-in thủ công**"
    if failed_users:
        result_text += f"\n\n⚠️ Lỗi: {', '.join(failed_users)}"
    result_text += f"\n\nBởi @{query.from_user.username}"

    await query.edit_message_text(result_text, parse_mode="Markdown")


def get_bulk_approve_handlers() -> list:
    """Trả về list handlers cho bulk approve.

    Returns:
        list: [CallbackQueryHandler]
    """
    return [
        CallbackQueryHandler(handle_bulk_approve, pattern=r"^bulk_approve_all$"),
    ]


# ============================================================
# B4: Admin NFC management
# ============================================================


async def admin_nfc_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Hiển thị danh sách NFC tokens, chọn action."""
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

    # Lấy danh sách NFC tokens
    tokens = list_nfc_tokens(office["id"])
    if tokens:
        token_list = "\n".join(
            f"  {i+1}. `{t['token']}` — {t.get('location', '(chưa đặt tên)')}"
            f" {'✅' if t.get('is_active') else '❌'} (ID: {t['id']})"
            for i, t in enumerate(tokens)
        )
    else:
        token_list = "  (chưa có NFC token nào)"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Tạo NFC token", callback_data="nfc_create"),
            InlineKeyboardButton("🗑️ Vô hiệu hóa", callback_data="nfc_deactivate"),
        ],
        [InlineKeyboardButton("❌ Đóng", callback_data="nfc_close")],
    ])

    await update.message.reply_text(
        f"🏷️ **NFC Tokens — {office['name']}**\n\n"
        f"{token_list}\n\n"
        f"Chọn hành động:",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
    return ADMIN_NFC_ACTION


async def admin_nfc_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Xử lý action từ NFC inline buttons."""
    query = update.callback_query
    await query.answer()

    if query.data == "nfc_close":
        await query.edit_message_text("👋 Đã đóng quản lý NFC.")
        return ConversationHandler.END

    if query.data == "nfc_create":
        context.user_data["nfc_action"] = "create"
        await query.edit_message_text(
            "🏷️ Nhập **mô tả vị trí** đặt NFC tag:\n"
            "Ví dụ: \"Cửa chính tầng 1\", \"Phòng họp A\"\n\n"
            "Hoặc /cancel để hủy.",
            parse_mode="Markdown",
        )
        return ADMIN_NFC_LOCATION

    if query.data == "nfc_deactivate":
        context.user_data["nfc_action"] = "deactivate"
        await query.edit_message_text(
            "🏷️ Nhập **ID** của NFC token muốn vô hiệu hóa:\n"
            "Hoặc /cancel để hủy.",
            parse_mode="Markdown",
        )
        return ADMIN_NFC_LOCATION

    return ConversationHandler.END


async def admin_nfc_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Nhận input cho NFC action (location hoặc token ID)."""
    action = context.user_data.get("nfc_action")
    text = update.message.text.strip()
    office_id = context.user_data.get("admin_office_id")

    if action == "create":
        if not office_id:
            await update.message.reply_text("❌ Không xác định được office.")
            return ConversationHandler.END

        nfc = create_nfc_token(office_id=office_id, location=text)
        deep_link = build_nfc_deep_link(nfc["token"])

        await update.message.reply_text(
            f"✅ **NFC Token đã tạo!**\n\n"
            f"🔑 Token: `{nfc['token']}`\n"
            f"📌 Vị trí: {text}\n"
            f"🔗 Deep link:\n`{deep_link}`\n\n"
            f"Ghi URL trên vào NFC tag (dạng NDEF URI record).",
            parse_mode="Markdown",
        )

    elif action == "deactivate":
        try:
            token_id = int(text)
        except ValueError:
            await update.message.reply_text("❌ Vui lòng nhập ID số nguyên:")
            return ADMIN_NFC_LOCATION

        result = deactivate_nfc_token(token_id)
        if result:
            await update.message.reply_text(f"✅ Đã vô hiệu hóa NFC token ID: {token_id}")
        else:
            await update.message.reply_text(f"❌ Không tìm thấy NFC token ID: {token_id}")

    return ConversationHandler.END


def get_admin_nfc_handler() -> ConversationHandler:
    """Tạo ConversationHandler cho NFC management.

    Returns:
        ConversationHandler: /admin_nfc handler.
    """
    return ConversationHandler(
        entry_points=[CommandHandler("admin_nfc", admin_nfc_command)],
        states={
            ADMIN_NFC_ACTION: [
                CallbackQueryHandler(admin_nfc_action, pattern=r"^nfc_"),
            ],
            ADMIN_NFC_LOCATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_nfc_input),
            ],
        },
        fallbacks=[CommandHandler("cancel", admin_cancel)],
    )

