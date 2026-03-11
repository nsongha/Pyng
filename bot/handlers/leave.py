"""Pyng — Leave Management Handlers.

C1: Leave request flow (/leave, /xinnghỉ) — ConversationHandler.
C2: Admin/Manager approve/reject leave — inline buttons.
C3: Xem số ngày phép còn lại (/phep).
"""

import logging
from datetime import date, datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.handlers._helpers import get_active_user_or_none
from services.leave_service import (
    create_leave_request,
    approve_leave,
    reject_leave,
    get_user_leaves,
    get_remaining_leave_days,
)
from services.user_service import is_admin, get_by_telegram_id
from config.settings import ADMIN_GROUP_ID
from config.timezone import get_tz

logger = logging.getLogger(__name__)

# Conversation states (range 400-405, không trùng với handlers khác)
CHOOSE_TYPE = 400
ENTER_START_DATE = 401
ENTER_END_DATE = 402
ENTER_REASON = 403
CONFIRM = 404

# Leave type mapping
LEAVE_TYPES = {
    "annual": "📅 Nghỉ phép năm",
    "sick": "💊 Nghỉ ốm",
    "compensatory": "🔄 Nghỉ bù",
    "unpaid": "🚫 Không lương",
}


# ============================================================
# C1: Leave Request ConversationHandler
# ============================================================


async def leave_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Bắt đầu leave request flow.

    Entry points: /leave, /xinnghỉ.
    """
    user = get_active_user_or_none(update.effective_user.id)
    if not user:
        await update.message.reply_text(
            "❌ Bạn chưa đăng ký hoặc chưa được duyệt.\n"
            "Gõ /start để đăng ký.",
        )
        return ConversationHandler.END

    context.user_data["leave_user"] = user

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📅 Nghỉ phép năm", callback_data="leave_type_annual"),
            InlineKeyboardButton("💊 Nghỉ ốm", callback_data="leave_type_sick"),
        ],
        [
            InlineKeyboardButton("🔄 Nghỉ bù", callback_data="leave_type_compensatory"),
            InlineKeyboardButton("🚫 Không lương", callback_data="leave_type_unpaid"),
        ],
        [InlineKeyboardButton("❌ Hủy", callback_data="leave_type_cancel")],
    ])

    # Lấy thông tin phép còn lại
    balance = get_remaining_leave_days(user["id"])

    await update.message.reply_text(
        "📋 **Xin nghỉ phép**\n\n"
        f"📊 Phép năm còn lại: **{balance['remaining']}/{balance['total']}** ngày\n\n"
        "Chọn loại nghỉ:",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
    return CHOOSE_TYPE


async def choose_leave_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Nhận loại nghỉ từ inline button."""
    query = update.callback_query
    await query.answer()

    if query.data == "leave_type_cancel":
        await query.edit_message_text("❌ Đã hủy xin nghỉ.")
        return ConversationHandler.END

    # Parse leave type: "leave_type_annual" → "annual"
    leave_type = query.data.replace("leave_type_", "")

    if leave_type not in LEAVE_TYPES:
        await query.edit_message_text("❌ Loại nghỉ không hợp lệ.")
        return ConversationHandler.END

    context.user_data["leave_type"] = leave_type

    await query.edit_message_text(
        f"📋 Loại nghỉ: **{LEAVE_TYPES[leave_type]}**\n\n"
        "Nhập **ngày bắt đầu** (DD/MM/YYYY):\n"
        "_Ví dụ: 15/03/2026_\n\n"
        "Hoặc /cancel để hủy.",
        parse_mode="Markdown",
    )
    return ENTER_START_DATE


async def enter_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Nhận ngày bắt đầu nghỉ."""
    text = update.message.text.strip()
    tz = get_tz()
    today = datetime.now(tz).date()

    try:
        start_date = datetime.strptime(text, "%d/%m/%Y").date()
    except ValueError:
        await update.message.reply_text(
            "❌ Sai định dạng. Nhập theo **DD/MM/YYYY**:\n"
            "_Ví dụ: 15/03/2026_",
            parse_mode="Markdown",
        )
        return ENTER_START_DATE

    if start_date < today:
        await update.message.reply_text(
            "❌ Ngày bắt đầu phải từ **hôm nay trở đi**.\n"
            "Nhập lại:",
            parse_mode="Markdown",
        )
        return ENTER_START_DATE

    context.user_data["leave_start_date"] = start_date

    await update.message.reply_text(
        f"📅 Ngày bắt đầu: **{start_date.strftime('%d/%m/%Y')}**\n\n"
        "Nhập **ngày kết thúc** (DD/MM/YYYY):\n"
        "_Nghỉ 1 ngày → nhập cùng ngày bắt đầu._\n\n"
        "Hoặc /cancel để hủy.",
        parse_mode="Markdown",
    )
    return ENTER_END_DATE


async def enter_end_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Nhận ngày kết thúc nghỉ."""
    text = update.message.text.strip()
    start_date = context.user_data.get("leave_start_date")

    try:
        end_date = datetime.strptime(text, "%d/%m/%Y").date()
    except ValueError:
        await update.message.reply_text(
            "❌ Sai định dạng. Nhập theo **DD/MM/YYYY**:",
            parse_mode="Markdown",
        )
        return ENTER_END_DATE

    if end_date < start_date:
        await update.message.reply_text(
            f"❌ Ngày kết thúc phải **≥ ngày bắt đầu** ({start_date.strftime('%d/%m/%Y')}).\n"
            "Nhập lại:",
            parse_mode="Markdown",
        )
        return ENTER_END_DATE

    context.user_data["leave_end_date"] = end_date

    await update.message.reply_text(
        f"📅 Nghỉ từ **{start_date.strftime('%d/%m/%Y')}** "
        f"→ **{end_date.strftime('%d/%m/%Y')}**\n\n"
        "Nhập **lý do** nghỉ (hoặc gõ `skip` để bỏ qua):\n\n"
        "Hoặc /cancel để hủy.",
        parse_mode="Markdown",
    )
    return ENTER_REASON


async def enter_reason(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Nhận lý do nghỉ, hiển thị xác nhận."""
    text = update.message.text.strip()
    reason = None if text.lower() == "skip" else text

    context.user_data["leave_reason"] = reason

    # Tóm tắt đơn
    leave_type = context.user_data["leave_type"]
    start_date = context.user_data["leave_start_date"]
    end_date = context.user_data["leave_end_date"]

    # Tính ngày làm việc
    from services.leave_service import _count_business_days
    days_count = _count_business_days(start_date, end_date)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Gửi đơn", callback_data="leave_confirm_yes"),
            InlineKeyboardButton("❌ Hủy", callback_data="leave_confirm_no"),
        ],
    ])

    await update.message.reply_text(
        "📋 **Xác nhận đơn xin nghỉ**\n\n"
        f"📌 Loại: {LEAVE_TYPES[leave_type]}\n"
        f"📅 Từ: {start_date.strftime('%d/%m/%Y')}\n"
        f"📅 Đến: {end_date.strftime('%d/%m/%Y')}\n"
        f"📊 Số ngày làm việc: **{days_count}** ngày\n"
        f"📝 Lý do: _{reason or '(không có)'}_\n\n"
        "Xác nhận gửi đơn?",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
    return CONFIRM


async def confirm_leave(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Xác nhận và tạo đơn nghỉ."""
    query = update.callback_query
    await query.answer()

    if query.data == "leave_confirm_no":
        await query.edit_message_text("❌ Đã hủy đơn xin nghỉ.")
        _cleanup_leave_data(context)
        return ConversationHandler.END

    # Tạo đơn
    user = context.user_data.get("leave_user")
    leave_type = context.user_data["leave_type"]
    start_date = context.user_data["leave_start_date"]
    end_date = context.user_data["leave_end_date"]
    reason = context.user_data.get("leave_reason")

    leave = create_leave_request(
        user_id=user["id"],
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        reason=reason,
    )

    leave_id = leave.get("id", "?")

    # Cập nhật message user
    await query.edit_message_text(
        "✅ **Đơn xin nghỉ đã gửi!**\n\n"
        f"📌 Mã đơn: #{leave_id}\n"
        f"📌 Loại: {LEAVE_TYPES[leave_type]}\n"
        f"📅 {start_date.strftime('%d/%m/%Y')} → {end_date.strftime('%d/%m/%Y')}\n"
        f"📊 Số ngày: {leave.get('days_count', '?')}\n\n"
        "⏳ Đang chờ admin/manager duyệt...\n"
        "Bạn sẽ nhận thông báo khi có kết quả.",
        parse_mode="Markdown",
    )

    # Gửi notification cho admin group
    admin_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Duyệt", callback_data=f"leave_approve_{leave_id}"),
            InlineKeyboardButton("❌ Từ chối", callback_data=f"leave_reject_{leave_id}"),
        ],
    ])

    admin_text = (
        f"📋 **Đơn xin nghỉ mới** (#{leave_id})\n\n"
        f"👤 {user['full_name']}"
    )
    if query.from_user.username:
        admin_text += f" (@{query.from_user.username})"
    admin_text += (
        f"\n📌 Loại: {LEAVE_TYPES[leave_type]}\n"
        f"📅 Từ: {start_date.strftime('%d/%m/%Y')}\n"
        f"📅 Đến: {end_date.strftime('%d/%m/%Y')}\n"
        f"📊 Số ngày: {leave.get('days_count', '?')}\n"
        f"📝 Lý do: _{reason or '(không có)'}_\n\n"
        "Duyệt hoặc từ chối:"
    )

    try:
        if ADMIN_GROUP_ID:
            await context.bot.send_message(
                chat_id=ADMIN_GROUP_ID,
                text=admin_text,
                parse_mode="Markdown",
                reply_markup=admin_keyboard,
            )
        else:
            logger.warning("ADMIN_GROUP_ID not configured, cannot send leave notification")
    except Exception as e:
        logger.error("Failed to send leave notification to admin: %s", e)

    _cleanup_leave_data(context)
    return ConversationHandler.END


async def leave_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Hủy leave request flow."""
    _cleanup_leave_data(context)
    await update.message.reply_text(
        "❌ Đã hủy. Gõ /leave để thử lại.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


def _cleanup_leave_data(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Dọn dẹp user_data sau khi flow kết thúc."""
    for key in ("leave_user", "leave_type", "leave_start_date", "leave_end_date", "leave_reason"):
        context.user_data.pop(key, None)


# ============================================================
# C2: Admin Approve/Reject Leave
# ============================================================


async def handle_leave_approval(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý khi admin bấm nút Duyệt đơn nghỉ."""
    query = update.callback_query

    if not is_admin(query.from_user.id):
        await query.answer("⛔ Bạn không có quyền admin.", show_alert=True)
        return

    await query.answer()

    # Parse leave_id từ callback_data: "leave_approve_42"
    leave_id = int(query.data.split("_")[2])

    # Lấy admin user ID trong bảng users
    admin_users = get_by_telegram_id(query.from_user.id)
    admin_user_id = admin_users["id"] if admin_users else None

    if not admin_user_id:
        await query.edit_message_text(
            (query.message.text or "") + "\n\n❌ Lỗi: Không tìm thấy admin trong hệ thống.",
        )
        return

    leave = approve_leave(leave_id, admin_user_id)

    if not leave:
        await query.edit_message_text(
            (query.message.text or "") + "\n\n⚠️ Đơn đã được xử lý trước đó.",
        )
        return

    # Cập nhật message admin
    await query.edit_message_text(
        (query.message.text or "")
        + f"\n\n✅ **Đã duyệt** bởi @{query.from_user.username}",
        parse_mode="Markdown",
    )

    # Notify user
    user_id = leave.get("user_id")
    if user_id:
        user_records = _get_user_by_id(user_id)
        if user_records:
            telegram_id = user_records.get("telegram_id")
            leave_type = leave.get("leave_type", "")
            type_label = LEAVE_TYPES.get(leave_type, leave_type)

            try:
                await context.bot.send_message(
                    chat_id=telegram_id,
                    text=(
                        f"✅ **Đơn nghỉ #{leave_id} đã được duyệt!**\n\n"
                        f"📌 Loại: {type_label}\n"
                        f"📅 {leave.get('start_date', '')} → {leave.get('end_date', '')}\n"
                        f"📊 Số ngày: {leave.get('days_count', '?')}\n\n"
                        "Chúc bạn nghỉ ngơi vui vẻ! 🎉"
                    ),
                    parse_mode="Markdown",
                )
            except Exception as e:
                logger.warning("Cannot notify user %s after leave approval: %s", telegram_id, e)


async def handle_leave_rejection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý khi admin bấm nút Từ chối đơn nghỉ."""
    query = update.callback_query

    if not is_admin(query.from_user.id):
        await query.answer("⛔ Bạn không có quyền admin.", show_alert=True)
        return

    await query.answer()

    leave_id = int(query.data.split("_")[2])

    # Lấy admin user ID
    admin_users = get_by_telegram_id(query.from_user.id)
    admin_user_id = admin_users["id"] if admin_users else None

    if not admin_user_id:
        await query.edit_message_text(
            (query.message.text or "") + "\n\n❌ Lỗi: Không tìm thấy admin trong hệ thống.",
        )
        return

    leave = reject_leave(leave_id, admin_user_id)

    if not leave:
        await query.edit_message_text(
            (query.message.text or "") + "\n\n⚠️ Đơn đã được xử lý trước đó.",
        )
        return

    # Cập nhật message admin
    await query.edit_message_text(
        (query.message.text or "")
        + f"\n\n❌ **Đã từ chối** bởi @{query.from_user.username}",
        parse_mode="Markdown",
    )

    # Notify user
    user_id = leave.get("user_id")
    if user_id:
        user_records = _get_user_by_id(user_id)
        if user_records:
            telegram_id = user_records.get("telegram_id")
            leave_type = leave.get("leave_type", "")
            type_label = LEAVE_TYPES.get(leave_type, leave_type)

            try:
                await context.bot.send_message(
                    chat_id=telegram_id,
                    text=(
                        f"❌ **Đơn nghỉ #{leave_id} bị từ chối.**\n\n"
                        f"📌 Loại: {type_label}\n"
                        f"📅 {leave.get('start_date', '')} → {leave.get('end_date', '')}\n\n"
                        "Liên hệ admin nếu cần hỗ trợ."
                    ),
                    parse_mode="Markdown",
                )
            except Exception as e:
                logger.warning("Cannot notify user %s after leave rejection: %s", telegram_id, e)


def _get_user_by_id(user_id: int) -> dict | None:
    """Lấy user record theo ID trong bảng users.

    Args:
        user_id: ID user (PK, không phải telegram_id).

    Returns:
        dict | None: User record hoặc None.
    """
    from db import client as db

    users = db.select("users", filters={"id": user_id}, limit=1)
    return users[0] if users else None


# ============================================================
# C3: Xem ngày phép (/phep)
# ============================================================


async def phep_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lệnh /phep — xem số ngày phép còn lại + lịch sử gần nhất."""
    user = get_active_user_or_none(update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ Bạn chưa đăng ký. Gõ /start.")
        return

    balance = get_remaining_leave_days(user["id"])
    recent_leaves = get_user_leaves(user["id"])[:5]  # 5 đơn gần nhất

    # Header
    text = (
        "📊 **Thông tin nghỉ phép**\n\n"
        f"👤 {user['full_name']}\n"
        f"📅 Tổng phép năm: **{balance['total']}** ngày\n"
        f"✅ Đã dùng: **{balance['used']}** ngày\n"
        f"💰 Còn lại: **{balance['remaining']}** ngày\n"
    )

    # Danh sách gần nhất
    if recent_leaves:
        text += "\n📋 **Đơn nghỉ gần nhất:**\n"
        for leave in recent_leaves:
            leave_type = leave.get("leave_type", "")
            type_label = LEAVE_TYPES.get(leave_type, leave_type)
            status = leave.get("status", "")
            status_icon = {"pending": "⏳", "approved": "✅", "rejected": "❌"}.get(status, "❓")

            text += (
                f"\n{status_icon} {type_label}\n"
                f"   📅 {leave.get('start_date', '')} → {leave.get('end_date', '')}"
                f" ({leave.get('days_count', '?')} ngày)\n"
            )
    else:
        text += "\n_Chưa có đơn nghỉ nào._\n"

    text += "\n💡 Gõ /leave để xin nghỉ mới."

    await update.message.reply_text(text, parse_mode="Markdown")


# ============================================================
# Handler factories
# ============================================================


def get_leave_request_handler() -> ConversationHandler:
    """Tạo ConversationHandler cho leave request flow.

    Entry points: /leave, /xinnghỉ (alias tiếng Việt).
    Flow: command → chọn loại → ngày bắt đầu → ngày kết thúc → lý do → xác nhận.

    Returns:
        ConversationHandler: Handler cho leave request.
    """
    return ConversationHandler(
        entry_points=[
            CommandHandler("leave", leave_command),
            CommandHandler("xinnghi", leave_command),
        ],
        states={
            CHOOSE_TYPE: [
                CallbackQueryHandler(choose_leave_type, pattern=r"^leave_type_"),
            ],
            ENTER_START_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_start_date),
            ],
            ENTER_END_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_end_date),
            ],
            ENTER_REASON: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_reason),
            ],
            CONFIRM: [
                CallbackQueryHandler(confirm_leave, pattern=r"^leave_confirm_"),
            ],
        },
        fallbacks=[CommandHandler("cancel", leave_cancel)],
    )


def get_leave_approval_handlers() -> list:
    """Trả về list handlers cho leave approval flow.

    Returns:
        list: [CallbackQueryHandler approve, CallbackQueryHandler reject].
    """
    return [
        CallbackQueryHandler(handle_leave_approval, pattern=r"^leave_approve_\d+$"),
        CallbackQueryHandler(handle_leave_rejection, pattern=r"^leave_reject_\d+$"),
    ]


def get_leave_balance_handler() -> CommandHandler:
    """Tạo CommandHandler cho /phep.

    Returns:
        CommandHandler: Handler xem ngày phép.
    """
    return CommandHandler("phep", phep_command)
