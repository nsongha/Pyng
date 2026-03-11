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
        "• `/report month` — Tổng hợp tháng + Excel\n\n"
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
