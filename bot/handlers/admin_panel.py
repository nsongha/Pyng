"""Pyng — Admin Panel Handlers (Phase 3).

Admin Panel mới — tách riêng khỏi admin.py (730 lines).
Callback prefix: ``ap_`` để tránh conflict với admin.py cũ.

Features:
    B1: Menu chính (/admin)
    B2: Quản lý nhân viên (list, edit role, deactivate)
    B3: Cài đặt hệ thống (giờ làm, toggle check-in methods)
    B4: Xem lịch sử check-in cá nhân
"""

import json
import logging
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from services.user_service import (
    is_admin,
    get_all_users,
    get_by_telegram_id,
    update_user,
    deactivate_user,
)
from services.config_service import get_config, set_config
from db import client as db
from config.settings import WORK_START, WORK_END, LATE_BUDGET_MINUTES
from config.timezone import get_tz

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Conversation states
# ------------------------------------------------------------------
PANEL_NAV = 200       # Tất cả callback navigation
PANEL_INPUT = 201     # Text input cho settings

# Pagination
PAGE_SIZE = 8

# Role display mapping
_ROLE_DISPLAY = {
    "admin": "👑 Admin",
    "manager": "📋 Manager",
    "employee": "👤 Employee",
}
_ROLE_ICON = {"admin": "👑", "manager": "📋", "employee": "👤"}


# ============================================================
# Helpers
# ============================================================


def _back_btn(callback_data: str = "ap_back") -> InlineKeyboardButton:
    """Nút quay lại."""
    return InlineKeyboardButton("⬅️ Quay lại", callback_data=callback_data)


# ============================================================
# B1: Main Menu (/admin)
# ============================================================


async def admin_panel_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Entry point: /admin → hiển thị menu chính."""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Bạn không có quyền admin.")
        return ConversationHandler.END

    return await _show_main_menu(update, context, via_message=True)


async def _show_main_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    via_message: bool = False,
) -> int:
    """Hiển thị admin panel menu chính."""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Quản lý nhân viên", callback_data="ap_menu_emp")],
        [InlineKeyboardButton("⚙️ Cài đặt hệ thống", callback_data="ap_menu_set")],
        [InlineKeyboardButton("📊 Báo cáo", callback_data="ap_menu_rpt")],
        [InlineKeyboardButton("✅ Duyệt thủ công", callback_data="ap_menu_apv")],
        [InlineKeyboardButton("🏢 Cài đặt văn phòng", callback_data="ap_menu_ofc")],
        [InlineKeyboardButton("❌ Đóng", callback_data="ap_close")],
    ])

    text = "👑 **Admin Panel — Pyng**\n\nChọn chức năng quản lý:"

    if via_message:
        await update.message.reply_text(
            text, parse_mode="Markdown", reply_markup=keyboard,
        )
    else:
        await update.callback_query.edit_message_text(
            text, parse_mode="Markdown", reply_markup=keyboard,
        )
    return PANEL_NAV


# ============================================================
# Callback Router (single handler cho tất cả navigation)
# ============================================================


async def panel_callback_router(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Router chính cho tất cả callback queries ``ap_*``."""
    query = update.callback_query
    await query.answer()
    data = query.data

    # -- Close --
    if data == "ap_close":
        await query.edit_message_text("👋 Đã đóng Admin Panel.")
        return ConversationHandler.END

    # -- Back to main menu --
    if data == "ap_back":
        return await _show_main_menu(update, context)

    # ----------------------------------------------------------
    # B1: Main menu navigation
    # ----------------------------------------------------------
    if data == "ap_menu_emp":
        return await _show_employee_list(update, context, page=0)

    if data == "ap_menu_set":
        return await _show_settings_menu(update, context)

    if data == "ap_menu_rpt":
        await query.edit_message_text(
            "📊 **Báo cáo**\n\n"
            "Tính năng báo cáo sẽ sẵn sàng sau khi hoàn thành Wave 3.\n"
            "Sử dụng `/report` khi tính năng được kích hoạt.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[_back_btn()]]),
        )
        return PANEL_NAV

    if data == "ap_menu_apv":
        await query.edit_message_text(
            "✅ **Duyệt thủ công**\n\n"
            "Khi nhân viên gửi yêu cầu check-in thủ công,\n"
            "notification sẽ gửi đến admin group với nút\n"
            "\"✅ Duyệt\" / \"❌ Từ chối\".\n\n"
            "Bạn không cần thao tác gì ở đây — chỉ cần chờ notification.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[_back_btn()]]),
        )
        return PANEL_NAV

    if data == "ap_menu_ofc":
        await query.edit_message_text(
            "🏢 **Cài đặt văn phòng**\n\n"
            "Sử dụng các lệnh:\n"
            "• `/admin_gps` — Cài đặt GPS / Geofence\n"
            "• `/admin_wifi` — Quản lý WiFi whitelist\n"
            "• `/admin_qr` — Cấu hình QR code\n"
            "• `/admin_nfc` — Quản lý NFC tokens",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[_back_btn()]]),
        )
        return PANEL_NAV

    # ----------------------------------------------------------
    # B2: Employee management
    # ----------------------------------------------------------
    if data.startswith("ap_emp_pg_"):
        page = int(data.split("_")[-1])
        return await _show_employee_list(update, context, page=page)

    if data == "ap_emp_back":
        return await _show_employee_list(update, context, page=0)

    if data.startswith("ap_emp_"):
        tid = int(data.split("_")[-1])
        return await _show_employee_detail(update, context, tid)

    if data.startswith("ap_role_"):
        tid = int(data.split("_")[-1])
        return await _show_role_menu(update, context, tid)

    # set role: ap_sr_{tid}_{role}
    if data.startswith("ap_sr_"):
        parts = data.split("_")
        tid = int(parts[2])
        role = parts[3]
        return await _execute_role_change(update, context, tid, role)

    # deactivate confirm / execute
    if data.startswith("ap_da_y_"):
        tid = int(data.split("_")[-1])
        return await _execute_deactivate(update, context, tid)

    if data.startswith("ap_da_n_"):
        tid = int(data.split("_")[-1])
        return await _show_employee_detail(update, context, tid)

    if data.startswith("ap_da_"):
        tid = int(data.split("_")[-1])
        return await _confirm_deactivate(update, context, tid)

    # ----------------------------------------------------------
    # B3: System settings
    # ----------------------------------------------------------
    if data == "ap_set_back":
        return await _show_settings_menu(update, context)

    if data == "ap_set_ws":
        context.user_data["ap_setting_key"] = "work_start"
        await query.edit_message_text(
            "🕐 **Sửa giờ bắt đầu làm việc**\n\n"
            "Nhập giờ mới (định dạng HH:MM):\n"
            "Ví dụ: `08:45`, `09:00`\n\n"
            "Hoặc /cancel để hủy.",
            parse_mode="Markdown",
        )
        return PANEL_INPUT

    if data == "ap_set_we":
        context.user_data["ap_setting_key"] = "work_end"
        await query.edit_message_text(
            "🕕 **Sửa giờ kết thúc làm việc**\n\n"
            "Nhập giờ mới (định dạng HH:MM):\n"
            "Ví dụ: `17:45`, `18:00`\n\n"
            "Hoặc /cancel để hủy.",
            parse_mode="Markdown",
        )
        return PANEL_INPUT

    if data == "ap_set_lb":
        context.user_data["ap_setting_key"] = "late_budget_minutes"
        await query.edit_message_text(
            "⏰ **Sửa quỹ đi muộn**\n\n"
            "Nhập số phút (mỗi tháng):\n"
            "Ví dụ: `180`, `120`\n\n"
            "Hoặc /cancel để hủy.",
            parse_mode="Markdown",
        )
        return PANEL_INPUT

    if data == "ap_set_m":
        return await _show_checkin_methods(update, context)

    if data.startswith("ap_set_tg_"):
        method = data.replace("ap_set_tg_", "")
        return await _toggle_checkin_method(update, context, method)

    # ----------------------------------------------------------
    # B4: Check-in history
    # ----------------------------------------------------------
    if data.startswith("ap_hi_pg_"):
        page = int(data.split("_")[-1])
        return await _show_history_list(update, context, page=page)

    if data == "ap_hi_back":
        return await _show_history_list(update, context, page=0)

    if data.startswith("ap_hi_"):
        tid = int(data.split("_")[-1])
        return await _show_user_checkin_history(update, context, tid)

    # Fallback
    return PANEL_NAV


# ============================================================
# B2: Employee Management
# ============================================================


async def _show_employee_list(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    page: int = 0,
) -> int:
    """Danh sách nhân viên có phân trang."""
    users = get_all_users()
    total = len(users)
    start = page * PAGE_SIZE
    end = min(start + PAGE_SIZE, total)
    page_users = users[start:end]
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

    buttons = []
    for u in page_users:
        status = "✅" if u.get("is_active") else "❌"
        icon = _ROLE_ICON.get(u.get("role", "employee"), "👤")
        name = u.get("full_name", "Unknown")[:20]
        tid = u["telegram_id"]
        buttons.append([
            InlineKeyboardButton(
                f"{status} {icon} {name}",
                callback_data=f"ap_emp_{tid}",
            ),
        ])

    # Pagination
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Trước", callback_data=f"ap_emp_pg_{page - 1}"))
    if end < total:
        nav.append(InlineKeyboardButton("Sau ➡️", callback_data=f"ap_emp_pg_{page + 1}"))
    if nav:
        buttons.append(nav)

    buttons.append([_back_btn()])

    await update.callback_query.edit_message_text(
        f"👥 **Quản lý nhân viên** ({total} người)\n"
        f"Trang {page + 1}/{total_pages}\n\n"
        "Chọn nhân viên để xem chi tiết:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return PANEL_NAV


async def _show_employee_detail(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    telegram_id: int,
) -> int:
    """Chi tiết một nhân viên."""
    user = get_by_telegram_id(telegram_id)
    if not user:
        await update.callback_query.edit_message_text(
            "❌ Không tìm thấy nhân viên.",
            reply_markup=InlineKeyboardMarkup([[_back_btn("ap_emp_back")]]),
        )
        return PANEL_NAV

    status = "✅ Active" if user.get("is_active") else "❌ Inactive"
    role = user.get("role", "employee")
    role_display = _ROLE_DISPLAY.get(role, role)
    department = user.get("department") or "Chưa set"
    created = str(user.get("created_at", "N/A"))[:10]
    leave_days = user.get("annual_leave_days", 12)

    text = (
        f"👤 **Chi tiết nhân viên**\n\n"
        f"📛 Tên: **{user.get('full_name', 'N/A')}**\n"
        f"📧 Email: {user.get('email', 'N/A')}\n"
        f"💬 Telegram: @{user.get('telegram_username') or 'N/A'}\n"
        f"🆔 ID: `{telegram_id}`\n"
        f"🎭 Role: {role_display}\n"
        f"🏢 Phòng ban: {department}\n"
        f"📊 Trạng thái: {status}\n"
        f"📅 Đăng ký: {created}\n"
        f"🌴 Ngày phép: {leave_days}"
    )

    buttons = [
        [InlineKeyboardButton("🎭 Đổi role", callback_data=f"ap_role_{telegram_id}")],
        [InlineKeyboardButton("📋 Lịch sử check-in", callback_data=f"ap_hi_{telegram_id}")],
    ]
    if user.get("is_active"):
        buttons.append([
            InlineKeyboardButton("🚫 Vô hiệu hóa", callback_data=f"ap_da_{telegram_id}"),
        ])
    buttons.append([_back_btn("ap_emp_back")])

    await update.callback_query.edit_message_text(
        text, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return PANEL_NAV


async def _show_role_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    telegram_id: int,
) -> int:
    """Menu chọn role mới."""
    user = get_by_telegram_id(telegram_id)
    current = user.get("role", "employee") if user else "employee"
    name = user.get("full_name", "N/A") if user else "N/A"

    roles = [("👤 Employee", "employee"), ("📋 Manager", "manager"), ("👑 Admin", "admin")]
    buttons = []
    for label, role in roles:
        prefix = "✓ " if role == current else ""
        buttons.append([
            InlineKeyboardButton(f"{prefix}{label}", callback_data=f"ap_sr_{telegram_id}_{role}"),
        ])
    buttons.append([_back_btn(f"ap_emp_{telegram_id}")])

    await update.callback_query.edit_message_text(
        f"🎭 **Đổi role — {name}**\n\n"
        f"Role hiện tại: **{current}**\nChọn role mới:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return PANEL_NAV


async def _execute_role_change(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    telegram_id: int,
    new_role: str,
) -> int:
    """Thực hiện đổi role."""
    valid_roles = {"employee", "manager", "admin"}
    if new_role not in valid_roles:
        await update.callback_query.edit_message_text(
            "❌ Role không hợp lệ.",
            reply_markup=InlineKeyboardMarkup([[_back_btn(f"ap_emp_{telegram_id}")]]),
        )
        return PANEL_NAV

    result = update_user(telegram_id, {"role": new_role})
    if result:
        display = _ROLE_DISPLAY.get(new_role, new_role)
        await update.callback_query.edit_message_text(
            f"✅ Đã đổi role thành **{display}**",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[_back_btn(f"ap_emp_{telegram_id}")]]),
        )
    else:
        await update.callback_query.edit_message_text(
            "❌ Lỗi đổi role. Thử lại sau.",
            reply_markup=InlineKeyboardMarkup([[_back_btn("ap_emp_back")]]),
        )
    return PANEL_NAV


async def _confirm_deactivate(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    telegram_id: int,
) -> int:
    """Xác nhận trước khi vô hiệu hóa."""
    user = get_by_telegram_id(telegram_id)
    name = user.get("full_name", "N/A") if user else "N/A"

    await update.callback_query.edit_message_text(
        f"⚠️ **Xác nhận vô hiệu hóa**\n\n"
        f"Bạn có chắc muốn vô hiệu hóa tài khoản **{name}**?\n"
        "Nhân viên sẽ không thể check-in sau khi bị vô hiệu hóa.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Xác nhận", callback_data=f"ap_da_y_{telegram_id}"),
                InlineKeyboardButton("❌ Hủy", callback_data=f"ap_da_n_{telegram_id}"),
            ],
        ]),
    )
    return PANEL_NAV


async def _execute_deactivate(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    telegram_id: int,
) -> int:
    """Thực hiện vô hiệu hóa tài khoản."""
    result = deactivate_user(telegram_id)
    if result:
        await update.callback_query.edit_message_text(
            "✅ Đã vô hiệu hóa tài khoản.",
            reply_markup=InlineKeyboardMarkup([[_back_btn("ap_emp_back")]]),
        )
    else:
        await update.callback_query.edit_message_text(
            "❌ Lỗi vô hiệu hóa. Thử lại sau.",
            reply_markup=InlineKeyboardMarkup([[_back_btn("ap_emp_back")]]),
        )
    return PANEL_NAV


# ============================================================
# B3: System Settings
# ============================================================


async def _show_settings_menu(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Hiển thị menu cài đặt hệ thống."""
    work_start = get_config("work_start") or WORK_START
    work_end = get_config("work_end") or WORK_END
    late_budget = get_config("late_budget_minutes") or str(LATE_BUDGET_MINUTES)

    text = (
        "⚙️ **Cài đặt hệ thống**\n\n"
        f"🕐 Giờ bắt đầu: **{work_start}**\n"
        f"🕕 Giờ kết thúc: **{work_end}**\n"
        f"⏰ Quỹ đi muộn: **{late_budget} phút/tháng**\n\n"
        "Chọn mục cần chỉnh sửa:"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🕐 Sửa giờ bắt đầu", callback_data="ap_set_ws")],
        [InlineKeyboardButton("🕕 Sửa giờ kết thúc", callback_data="ap_set_we")],
        [InlineKeyboardButton("⏰ Sửa quỹ đi muộn", callback_data="ap_set_lb")],
        [InlineKeyboardButton("📱 Phương thức check-in", callback_data="ap_set_m")],
        [_back_btn()],
    ])

    await update.callback_query.edit_message_text(
        text, parse_mode="Markdown", reply_markup=keyboard,
    )
    return PANEL_NAV


async def panel_text_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Xử lý text input cho settings (PANEL_INPUT state)."""
    key = context.user_data.get("ap_setting_key")
    text = update.message.text.strip()
    admin_id = update.effective_user.id

    # -- Validate --
    if key in ("work_start", "work_end"):
        parts = text.split(":")
        if len(parts) != 2:
            await update.message.reply_text("❌ Sai định dạng. Nhập lại (HH:MM):")
            return PANEL_INPUT
        try:
            h, m = int(parts[0]), int(parts[1])
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError
            text = f"{h:02d}:{m:02d}"
        except ValueError:
            await update.message.reply_text("❌ Giờ không hợp lệ. Nhập lại (HH:MM):")
            return PANEL_INPUT

    elif key == "late_budget_minutes":
        try:
            minutes = int(text)
            if minutes < 0 or minutes > 999:
                raise ValueError
            text = str(minutes)
        except ValueError:
            await update.message.reply_text("❌ Nhập số phút hợp lệ (0-999):")
            return PANEL_INPUT

    # -- Save --
    set_config(key, text, admin_id)

    label = {
        "work_start": "Giờ bắt đầu",
        "work_end": "Giờ kết thúc",
        "late_budget_minutes": "Quỹ đi muộn",
    }.get(key, key)

    await update.message.reply_text(
        f"✅ Đã cập nhật **{label}**: `{text}`\n\n"
        "Gõ /admin để quay lại menu.",
        parse_mode="Markdown",
    )
    return ConversationHandler.END


async def _show_checkin_methods(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Hiển thị toggle bật/tắt phương thức check-in."""
    methods_json = get_config("checkin_methods_enabled")
    if methods_json:
        try:
            enabled = json.loads(methods_json)
        except (json.JSONDecodeError, TypeError):
            enabled = ["gps", "wifi", "qr", "nfc", "manual"]
    else:
        enabled = ["gps", "wifi", "qr", "nfc", "manual"]

    methods = [
        ("📍 GPS", "gps"),
        ("📶 WiFi", "wifi"),
        ("📱 QR Code", "qr"),
        ("🏷️ NFC", "nfc"),
        ("✋ Manual", "manual"),
    ]

    buttons = []
    for label, key in methods:
        toggle = "✅" if key in enabled else "❌"
        buttons.append([
            InlineKeyboardButton(f"{toggle} {label}", callback_data=f"ap_set_tg_{key}"),
        ])
    buttons.append([_back_btn("ap_set_back")])

    await update.callback_query.edit_message_text(
        "📱 **Phương thức check-in**\n\n"
        "Bật/tắt từng phương thức:\n"
        "(✅ = bật, ❌ = tắt)",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return PANEL_NAV


async def _toggle_checkin_method(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    method: str,
) -> int:
    """Bật/tắt một phương thức check-in."""
    methods_json = get_config("checkin_methods_enabled")
    if methods_json:
        try:
            enabled = json.loads(methods_json)
        except (json.JSONDecodeError, TypeError):
            enabled = ["gps", "wifi", "qr", "nfc", "manual"]
    else:
        enabled = ["gps", "wifi", "qr", "nfc", "manual"]

    if method in enabled:
        enabled.remove(method)
    else:
        enabled.append(method)

    set_config("checkin_methods_enabled", json.dumps(enabled), update.effective_user.id)

    # Refresh lại màn hình toggle
    return await _show_checkin_methods(update, context)


# ============================================================
# B4: Check-in History
# ============================================================


async def _show_history_list(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    page: int = 0,
) -> int:
    """Danh sách NV active để xem lịch sử (dùng từ menu chính, nếu cần)."""
    users = [u for u in get_all_users() if u.get("is_active")]
    total = len(users)
    start = page * PAGE_SIZE
    end = min(start + PAGE_SIZE, total)
    page_users = users[start:end]
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

    buttons = []
    for u in page_users:
        name = u.get("full_name", "Unknown")[:25]
        tid = u["telegram_id"]
        buttons.append([
            InlineKeyboardButton(f"👤 {name}", callback_data=f"ap_hi_{tid}"),
        ])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Trước", callback_data=f"ap_hi_pg_{page - 1}"))
    if end < total:
        nav.append(InlineKeyboardButton("Sau ➡️", callback_data=f"ap_hi_pg_{page + 1}"))
    if nav:
        buttons.append(nav)

    buttons.append([_back_btn()])

    await update.callback_query.edit_message_text(
        f"📋 **Lịch sử check-in**\n"
        f"Trang {page + 1}/{total_pages}\n\n"
        "Chọn nhân viên:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return PANEL_NAV


async def _show_user_checkin_history(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    telegram_id: int,
) -> int:
    """Hiển thị 30 ngày check-in gần nhất của một nhân viên."""
    user = get_by_telegram_id(telegram_id)
    if not user:
        await update.callback_query.edit_message_text(
            "❌ Không tìm thấy nhân viên.",
            reply_markup=InlineKeyboardMarkup([[_back_btn("ap_emp_back")]]),
        )
        return PANEL_NAV

    # Query 30 ngày gần nhất
    tz = get_tz()
    now = datetime.now(tz)
    since = (now - timedelta(days=30)).isoformat()

    checkins = db.select(
        "checkins",
        filters={
            "user_id": user["id"],
            "checked_at.gte": since,
        },
        order="checked_at.desc",
        limit=62,  # ~2 records/day × 31
    )

    name = user.get("full_name", "N/A")

    if not checkins:
        await update.callback_query.edit_message_text(
            f"📋 **{name}** — 30 ngày gần nhất\n\n"
            "Không có lịch sử check-in.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[_back_btn(f"ap_emp_{telegram_id}")]]),
        )
        return PANEL_NAV

    # Group theo ngày
    days: dict[str, dict] = {}
    for c in checkins:
        date_str = c.get("checked_at", "")[:10]
        if date_str not in days:
            days[date_str] = {"in": None, "out": None, "method": ""}
        if c["type"] == "in":
            days[date_str]["in"] = c.get("checked_at", "")[11:16]
            days[date_str]["method"] = c.get("method", "")
        elif c["type"] == "out":
            days[date_str]["out"] = c.get("checked_at", "")[11:16]

    # Build text (giới hạn 15 dòng tránh message quá dài)
    work_start = get_config("work_start") or WORK_START
    ws_parts = work_start.split(":")
    ws_min = int(ws_parts[0]) * 60 + int(ws_parts[1])

    lines = []
    sorted_days = sorted(days.items(), reverse=True)
    for date_str, info in sorted_days[:15]:
        time_in = info["in"] or "——"
        time_out = info["out"] or "——"
        method = info["method"].upper()[:3] if info["method"] else "—"

        status = ""
        if info["in"]:
            in_parts = info["in"].split(":")
            in_min = int(in_parts[0]) * 60 + int(in_parts[1])
            status = "🔰" if in_min <= ws_min + 5 else "⏰"

        lines.append(f"`{date_str}` {time_in}→{time_out} {method} {status}")

    text = f"📋 **{name}** — 30 ngày\n\n" + "\n".join(lines)

    if len(sorted_days) > 15:
        text += f"\n\n_… và {len(sorted_days) - 15} ngày nữa_"

    await update.callback_query.edit_message_text(
        text, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[_back_btn(f"ap_emp_{telegram_id}")]]),
    )
    return PANEL_NAV


# ============================================================
# Cancel
# ============================================================


async def admin_panel_cancel(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Hủy admin panel flow."""
    await update.message.reply_text("❌ Đã đóng Admin Panel.")
    return ConversationHandler.END


# ============================================================
# Handler factory
# ============================================================


def get_admin_panel_handlers() -> list:
    """Trả về list handlers cho admin panel.

    Returns:
        list: [ConversationHandler] cho ``/admin`` command.
    """
    conv = ConversationHandler(
        entry_points=[CommandHandler("admin", admin_panel_command)],
        states={
            PANEL_NAV: [
                CallbackQueryHandler(panel_callback_router, pattern=r"^ap_"),
            ],
            PANEL_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, panel_text_input),
            ],
        },
        fallbacks=[CommandHandler("cancel", admin_panel_cancel)],
    )
    return [conv]
