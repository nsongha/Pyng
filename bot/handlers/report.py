"""Pyng — Report Handlers.

D2: Report bot commands (/report today|week|month) — admin-only.
D3: Weekly/Monthly Excel export (gửi trực tiếp qua Telegram).
"""

import io
import logging
from datetime import datetime, date, timedelta

from telegram import Update
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    filters,
)

from bot.handlers._helpers import get_active_user_or_none
from services.user_service import is_admin
from services.report_service import (
    generate_daily_text_report,
    get_weekly_report_data,
    generate_monthly_excel,
    generate_custom_range_excel,
)
from config.timezone import get_tz

logger = logging.getLogger(__name__)


# ============================================================
# D2: Report Commands
# ============================================================


async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lệnh /report — báo cáo cho admin.

    Usage:
        /report today  — báo cáo hôm nay (text)
        /report week   — tổng hợp tuần này (text)
        /report month  — tổng hợp tháng + gửi Excel file

    Admin-only.
    """
    user = get_active_user_or_none(update.effective_user.id)
    if not user:
        await update.message.reply_text("❌ Bạn chưa đăng ký. Gõ /start.")
        return

    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Chỉ admin mới dùng được lệnh này.")
        return

    # Parse sub-command
    args = context.args
    if not args:
        await _show_report_usage(update)
        return

    # Custom date range: /report YYYY-MM-DD YYYY-MM-DD
    if len(args) == 2 and "-" in args[0] and "-" in args[1]:
        await _report_custom_range(update, args[0], args[1])
        return

    sub_command = args[0].lower()

    if sub_command == "today":
        await _report_today(update)
    elif sub_command == "week":
        await _report_week(update)
    elif sub_command == "month":
        await _report_month(update, context)
    else:
        await _show_report_usage(update)


async def _show_report_usage(update: Update) -> None:
    """Hiển thị hướng dẫn sử dụng /report."""
    await update.message.reply_text(
        "📊 **Báo cáo** — Hướng dẫn\n\n"
        "Cách dùng:\n"
        "• `/report today` — Báo cáo hôm nay\n"
        "• `/report week` — Tổng hợp tuần\n"
        "• `/report month` — Tổng hợp tháng + Excel\n"
        "• `/report YYYY-MM-DD YYYY-MM-DD` — Excel khoảng ngày\n\n"
        "Ví dụ: `/report 2026-03-01 2026-03-10`\n\n"
        "Alias: `/baocao`",
        parse_mode="Markdown",
    )


# ============================================================
# D2: /report today
# ============================================================


async def _report_today(update: Update) -> None:
    """Báo cáo hôm nay — text summary."""
    await update.message.reply_text("⏳ Đang tạo báo cáo...")

    try:
        report_text = generate_daily_text_report()
        await update.message.reply_text(report_text, parse_mode="Markdown")
    except Exception as e:
        logger.exception("Error generating daily report")
        await update.message.reply_text("❌ Lỗi khi tạo báo cáo. Thử lại sau.")


# ============================================================
# D2: /report week
# ============================================================


async def _report_week(update: Update) -> None:
    """Tổng hợp tuần này — text summary."""
    await update.message.reply_text("⏳ Đang tạo báo cáo tuần...")

    try:
        data = get_weekly_report_data()
        text = _format_weekly_text(data)
        await update.message.reply_text(text, parse_mode="Markdown")
    except Exception as e:
        logger.exception("Error generating weekly report")
        await update.message.reply_text("❌ Lỗi khi tạo báo cáo tuần. Thử lại sau.")


def _format_weekly_text(data: dict) -> str:
    """Format weekly report data thành text cho Telegram.

    Args:
        data: Dict từ get_weekly_report_data().

    Returns:
        str: Formatted text report.
    """
    lines = [
        f"📊 *Báo cáo tuần: {data['start_date']} → {data['end_date']}*",
        "",
    ]

    summary = data.get("summary", {})

    if not summary:
        lines.append("_Không có dữ liệu._")
        return "\n".join(lines)

    # Header
    lines.append("```")
    lines.append(f"{'Tên':<20} {'Đi':>3} {'Muộn':>5} {'WFH':>4} {'Phép':>5} {'Vắng':>5}")
    lines.append("─" * 46)

    for uid, stats in summary.items():
        name = stats["name"]
        # Truncate tên nếu quá dài
        if len(name) > 18:
            name = name[:17] + "…"
        lines.append(
            f"{name:<20} {stats['present']:>3} "
            f"{stats['late']:>5} {stats['wfh']:>4} "
            f"{stats['on_leave']:>5} {stats['absent']:>5}"
        )

    lines.append("```")

    # Totals
    total_users = len(summary)
    lines.append(f"\n👥 Tổng nhân viên: *{total_users}*")

    return "\n".join(lines)


# ============================================================
# D3: /report month — Text summary + Excel file
# ============================================================


async def _report_month(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tổng hợp tháng hiện tại — text + Excel file."""
    await update.message.reply_text("⏳ Đang tạo báo cáo tháng + file Excel...")

    tz = get_tz()
    now = datetime.now(tz)
    month = now.month
    year = now.year

    try:
        # 1. Text summary cho tháng này
        first_day = date(year, month, 1)
        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)

        data = get_weekly_report_data(first_day, last_day)
        text = _format_monthly_text(data, month, year)
        await update.message.reply_text(text, parse_mode="Markdown")

        # 2. Excel file
        excel_bytes = generate_monthly_excel(month, year)
        filename = f"Pyng_Report_{year}_{month:02d}.xlsx"

        await update.message.reply_document(
            document=io.BytesIO(excel_bytes),
            filename=filename,
            caption=f"📎 Báo cáo chi tiết tháng {month}/{year}",
        )

    except Exception as e:
        logger.exception("Error generating monthly report")
        await update.message.reply_text("❌ Lỗi khi tạo báo cáo tháng. Thử lại sau.")


def _format_monthly_text(data: dict, month: int, year: int) -> str:
    """Format monthly report data thành text cho Telegram.

    Args:
        data: Dict từ get_weekly_report_data() (dùng cho cả tháng).
        month: Tháng.
        year: Năm.

    Returns:
        str: Formatted text report.
    """
    lines = [
        f"📊 *Báo cáo tháng {month}/{year}*",
        f"📅 Từ {data['start_date']} → {data['end_date']}",
        "",
    ]

    summary = data.get("summary", {})

    if not summary:
        lines.append("_Không có dữ liệu._")
        return "\n".join(lines)

    # Summary table
    lines.append("```")
    lines.append(f"{'Tên':<20} {'Đi':>3} {'Muộn':>5} {'WFH':>4} {'Phép':>5} {'Vắng':>5}")
    lines.append("─" * 46)

    for uid, stats in summary.items():
        name = stats["name"]
        if len(name) > 18:
            name = name[:17] + "…"
        lines.append(
            f"{name:<20} {stats['present']:>3} "
            f"{stats['late']:>5} {stats['wfh']:>4} "
            f"{stats['on_leave']:>5} {stats['absent']:>5}"
        )

    lines.append("```")

    total_users = len(summary)
    lines.append(f"\n👥 Tổng nhân viên: *{total_users}*")
    lines.append("\n📎 _File Excel đang được gửi..._")

    return "\n".join(lines)

# ============================================================
# A3: /report YYYY-MM-DD YYYY-MM-DD — Custom date range
# ============================================================


async def _report_custom_range(update: Update, start_str: str, end_str: str) -> None:
    """Báo cáo theo khoảng ngày tùy chọn — Excel file.

    Args:
        update: Telegram update.
        start_str: Ngày bắt đầu dạng YYYY-MM-DD.
        end_str: Ngày kết thúc dạng YYYY-MM-DD.
    """
    # Validate date format
    try:
        start_date = date.fromisoformat(start_str)
        end_date = date.fromisoformat(end_str)
    except ValueError:
        await update.message.reply_text(
            "❌ Định dạng ngày không hợp lệ.\n"
            "Dùng: `/report YYYY-MM-DD YYYY-MM-DD`\n"
            "Ví dụ: `/report 2026-03-01 2026-03-10`",
            parse_mode="Markdown",
        )
        return

    if end_date < start_date:
        await update.message.reply_text("❌ Ngày kết thúc phải >= ngày bắt đầu.")
        return

    range_days = (end_date - start_date).days + 1
    if range_days > 90:
        await update.message.reply_text(
            f"❌ Khoảng ngày quá dài: {range_days} ngày.\n"
            f"Tối đa 90 ngày."
        )
        return

    await update.message.reply_text(
        f"⏳ Đang tạo báo cáo {start_str} → {end_str} ({range_days} ngày)..."
    )

    try:
        excel_bytes = generate_custom_range_excel(start_date, end_date)
        filename = f"Pyng_Report_{start_str}_{end_str}.xlsx"

        await update.message.reply_document(
            document=io.BytesIO(excel_bytes),
            filename=filename,
            caption=f"📎 Báo cáo {start_str} → {end_str}",
        )
    except ValueError as e:
        await update.message.reply_text(f"❌ {e}")
    except Exception as e:
        logger.exception("Error generating custom range report")
        await update.message.reply_text("❌ Lỗi khi tạo báo cáo. Thử lại sau.")


# ============================================================
# Handler factories
# ============================================================


def get_report_handlers() -> list:
    """Trả về list handlers cho report commands.

    Commands: /report, /baocao (alias tiếng Việt).

    Returns:
        list: [CommandHandler].
    """
    return [
        CommandHandler("report", report_command),
        CommandHandler("baocao", report_command),
    ]
