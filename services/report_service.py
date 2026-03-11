"""Pyng — Report Service.

Aggregate data từ checkins + leaves + users để tạo báo cáo.
Hỗ trợ: daily text report, weekly summary, monthly Excel export.

Dependencies:
    - services/checkin_service (reuse time range patterns)
    - services/leave_service (users on leave)
    - services/user_service (active user list)
    - openpyxl (Excel generation)
    - config/settings (WORK_START cho ontime check)
"""

import io
import logging
from datetime import date, datetime, timedelta

from db import client as db
from config.settings import WORK_START
from config.timezone import get_tz

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _date_range(target_date: date) -> tuple[str, str]:
    """Trả về (start, end) ISO string cho 1 ngày cụ thể.

    Args:
        target_date: Ngày cần lấy range.

    Returns:
        tuple: (start_iso, end_iso).
    """
    tz = get_tz()
    start = datetime(
        target_date.year, target_date.month, target_date.day,
        0, 0, 0, tzinfo=tz,
    )
    end = start + timedelta(days=1)
    return start.isoformat(), end.isoformat()


def _is_late(checked_at_str: str) -> bool:
    """Kiểm tra check-in có muộn không (so với WORK_START + 5 phút grace).

    Args:
        checked_at_str: ISO timestamp string từ DB.

    Returns:
        bool: True nếu đi muộn.
    """
    tz = get_tz()
    checked_at = datetime.fromisoformat(checked_at_str)
    if checked_at.tzinfo is None:
        checked_at = checked_at.replace(tzinfo=tz)

    parts = WORK_START.split(":")
    work_start_minutes = int(parts[0]) * 60 + int(parts[1])
    checkin_minutes = checked_at.hour * 60 + checked_at.minute

    return checkin_minutes > work_start_minutes + 5  # 5 phút grace


# ------------------------------------------------------------------
# Daily Report
# ------------------------------------------------------------------

def get_daily_report_data(target_date: date | None = None) -> dict:
    """Lấy dữ liệu báo cáo ngày.

    Args:
        target_date: Ngày cần báo cáo. None = hôm nay.

    Returns:
        dict: {
            "date": str,
            "present": list[dict],   — users đã check-in tại VP
            "wfh": list[dict],       — users WFH
            "late": list[dict],      — users đi muộn (subset of present)
            "on_leave": list[dict],  — users đang nghỉ phép
            "absent": list[dict],    — users không có mặt, không nghỉ
        }
    """
    tz = get_tz()
    if target_date is None:
        target_date = datetime.now(tz).date()

    start, end = _date_range(target_date)

    # 1. Lấy tất cả active users
    all_users = db.select("users", filters={"is_active": True})
    user_map = {u["id"]: u for u in all_users}

    # 2. Lấy checkins hôm đó (type = 'in')
    checkins = db.select(
        "checkins",
        filters={
            "type": "in",
            "checked_at.gte": start,
            "checked_at.lt": end,
        },
        order="checked_at.asc",
    )

    # 3. Lấy leaves overlap ngày này (approved)
    date_str = target_date.isoformat()
    on_leave_records = db.select(
        "leaves",
        filters={
            "status": "approved",
            "start_date.lte": date_str,
            "end_date.gte": date_str,
        },
    )
    on_leave_user_ids = {rec["user_id"] for rec in on_leave_records}

    # 4. Phân loại
    present = []
    wfh = []
    late = []
    checked_in_user_ids = set()

    for ci in checkins:
        uid = ci["user_id"]
        if uid in checked_in_user_ids:
            continue  # chỉ lấy lần check-in đầu tiên
        checked_in_user_ids.add(uid)

        user = user_map.get(uid)
        if not user:
            continue

        entry = {
            "user": user,
            "checkin": ci,
        }

        if ci.get("method") == "wfh":
            wfh.append(entry)
        else:
            present.append(entry)
            if _is_late(ci["checked_at"]):
                late.append(entry)

    # 5. On leave (có user info)
    on_leave = [
        {"user": user_map[uid], "leave": rec}
        for rec in on_leave_records
        if (uid := rec["user_id"]) in user_map
    ]

    # 6. Absent = active users - present - wfh - on_leave
    accounted_ids = checked_in_user_ids | on_leave_user_ids
    absent = [
        {"user": user_map[uid]}
        for uid in user_map
        if uid not in accounted_ids
    ]

    return {
        "date": target_date.isoformat(),
        "present": present,
        "wfh": wfh,
        "late": late,
        "on_leave": on_leave,
        "absent": absent,
    }


def generate_daily_text_report(target_date: date | None = None) -> str:
    """Tạo text report cho Telegram (daily summary).

    Args:
        target_date: Ngày cần báo cáo. None = hôm nay.

    Returns:
        str: Formatted text report.
    """
    data = get_daily_report_data(target_date)

    lines = [
        f"📊 *Báo cáo ngày {data['date']}*",
        "",
        f"✅ Có mặt: *{len(data['present'])}*",
        f"🏠 WFH: *{len(data['wfh'])}*",
        f"❌ Vắng: *{len(data['absent'])}*",
        f"⏰ Muộn: *{len(data['late'])}*",
        f"📋 Nghỉ phép: *{len(data['on_leave'])}*",
        "",
    ]

    # Chi tiết từng nhóm
    if data["present"]:
        lines.append("*✅ Có mặt:*")
        for entry in data["present"]:
            user = entry["user"]
            ci = entry["checkin"]
            time_str = _format_checkin_time(ci["checked_at"])
            method = ci.get("method", "")
            late_mark = " ⏰" if entry in data["late"] else ""
            lines.append(f"  • {user['full_name']} — {time_str} ({method}){late_mark}")
        lines.append("")

    if data["wfh"]:
        lines.append("*🏠 WFH:*")
        for entry in data["wfh"]:
            lines.append(f"  • {entry['user']['full_name']}")
        lines.append("")

    if data["on_leave"]:
        lines.append("*📋 Nghỉ phép:*")
        for entry in data["on_leave"]:
            leave = entry["leave"]
            leave_type_map = {
                "annual": "Phép năm",
                "sick": "Ốm",
                "compensatory": "Nghỉ bù",
                "unpaid": "Không lương",
            }
            lt = leave_type_map.get(leave.get("leave_type", ""), leave.get("leave_type", ""))
            lines.append(f"  • {entry['user']['full_name']} — {lt}")
        lines.append("")

    if data["absent"]:
        lines.append("*❌ Vắng (chưa check-in):*")
        for entry in data["absent"]:
            lines.append(f"  • {entry['user']['full_name']}")
        lines.append("")

    return "\n".join(lines)


def _format_checkin_time(checked_at_str: str) -> str:
    """Format checkin timestamp thành HH:MM.

    Args:
        checked_at_str: ISO timestamp.

    Returns:
        str: Time string "HH:MM".
    """
    tz = get_tz()
    dt = datetime.fromisoformat(checked_at_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    return dt.strftime("%H:%M")


# ------------------------------------------------------------------
# Weekly Report
# ------------------------------------------------------------------

def get_weekly_report_data(
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    """Aggregate data tuần.

    Args:
        start_date: Ngày đầu tuần. None = Monday tuần này.
        end_date: Ngày cuối tuần. None = tính từ start_date + 6.

    Returns:
        dict: {
            "start_date": str,
            "end_date": str,
            "summary": {user_id: {name, present, wfh, late, on_leave, absent}},
        }
    """
    tz = get_tz()
    today = datetime.now(tz).date()

    if start_date is None:
        # Monday tuần này
        start_date = today - timedelta(days=today.weekday())
    if end_date is None:
        end_date = start_date + timedelta(days=4)  # Friday

    # Aggregate daily data
    summary: dict[int, dict] = {}
    current = start_date

    while current <= end_date:
        # Chỉ tính ngày làm việc
        if current.weekday() >= 5:
            current += timedelta(days=1)
            continue

        daily = get_daily_report_data(current)

        # Init summary cho tất cả users
        all_user_ids = set()
        for group in ["present", "wfh", "on_leave", "absent"]:
            for entry in daily[group]:
                uid = entry["user"]["id"]
                all_user_ids.add(uid)
                if uid not in summary:
                    summary[uid] = {
                        "name": entry["user"]["full_name"],
                        "present": 0,
                        "wfh": 0,
                        "late": 0,
                        "on_leave": 0,
                        "absent": 0,
                    }

        # Count
        for entry in daily["present"]:
            summary[entry["user"]["id"]]["present"] += 1
        for entry in daily["wfh"]:
            summary[entry["user"]["id"]]["wfh"] += 1
        for entry in daily["late"]:
            summary[entry["user"]["id"]]["late"] += 1
        for entry in daily["on_leave"]:
            summary[entry["user"]["id"]]["on_leave"] += 1
        for entry in daily["absent"]:
            summary[entry["user"]["id"]]["absent"] += 1

        current += timedelta(days=1)

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "summary": summary,
    }


# ------------------------------------------------------------------
# Monthly Excel
# ------------------------------------------------------------------

def generate_monthly_excel(month: int, year: int) -> bytes:
    """Tạo Excel report tháng.

    Sheet 1 "Tổng hợp": tên, số ngày đi, muộn, WFH, nghỉ phép.
    Sheet 2 "Chi tiết": từng ngày, giờ in/out, method, status.

    Args:
        month: Tháng (1-12).
        year: Năm.

    Returns:
        bytes: Excel file content (openpyxl workbook).
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill

    wb = Workbook()

    # ── Sheet 1: Tổng hợp ──
    ws_summary = wb.active
    ws_summary.title = "Tổng hợp"

    # Header styling
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")

    headers = ["STT", "Họ tên", "Số ngày đi", "Muộn", "WFH", "Nghỉ phép", "Vắng"]
    for col_idx, header in enumerate(headers, 1):
        cell = ws_summary.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    # Tính ngày đầu/cuối tháng
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    weekly_data = get_weekly_report_data(first_day, last_day)

    row_idx = 2
    for stt, (uid, stats) in enumerate(weekly_data["summary"].items(), 1):
        ws_summary.cell(row=row_idx, column=1, value=stt)
        ws_summary.cell(row=row_idx, column=2, value=stats["name"])
        ws_summary.cell(row=row_idx, column=3, value=stats["present"])
        ws_summary.cell(row=row_idx, column=4, value=stats["late"])
        ws_summary.cell(row=row_idx, column=5, value=stats["wfh"])
        ws_summary.cell(row=row_idx, column=6, value=stats["on_leave"])
        ws_summary.cell(row=row_idx, column=7, value=stats["absent"])
        row_idx += 1

    # Auto-fit column widths (approximate)
    ws_summary.column_dimensions["A"].width = 6
    ws_summary.column_dimensions["B"].width = 25
    for col_letter in ["C", "D", "E", "F", "G"]:
        ws_summary.column_dimensions[col_letter].width = 12

    # ── Sheet 2: Chi tiết ──
    ws_detail = wb.create_sheet("Chi tiết")

    detail_headers = ["Ngày", "Họ tên", "Giờ vào", "Giờ ra", "Phương thức", "Trạng thái"]
    for col_idx, header in enumerate(detail_headers, 1):
        cell = ws_detail.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    detail_row = 2
    current_date = first_day
    tz = get_tz()

    while current_date <= last_day:
        if current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue

        start_iso, end_iso = _date_range(current_date)

        # Check-ins
        checkins = db.select(
            "checkins",
            filters={
                "type": "in",
                "checked_at.gte": start_iso,
                "checked_at.lt": end_iso,
            },
            order="checked_at.asc",
        )

        # Check-outs
        checkouts = db.select(
            "checkins",
            filters={
                "type": "out",
                "checked_at.gte": start_iso,
                "checked_at.lt": end_iso,
            },
            order="checked_at.asc",
        )
        checkout_map = {co["user_id"]: co for co in checkouts}

        # Users
        all_users = db.select("users", filters={"is_active": True})
        user_map = {u["id"]: u for u in all_users}

        # Ghi users đã check-in
        checked_user_ids = set()
        for ci in checkins:
            uid = ci["user_id"]
            if uid in checked_user_ids:
                continue
            checked_user_ids.add(uid)

            user = user_map.get(uid)
            if not user:
                continue

            time_in = _format_checkin_time(ci["checked_at"])
            co = checkout_map.get(uid)
            time_out = _format_checkin_time(co["checked_at"]) if co else "—"
            method = ci.get("method", "")
            status = "Muộn" if _is_late(ci["checked_at"]) else "Đúng giờ"

            ws_detail.cell(row=detail_row, column=1, value=current_date.strftime("%d/%m"))
            ws_detail.cell(row=detail_row, column=2, value=user["full_name"])
            ws_detail.cell(row=detail_row, column=3, value=time_in)
            ws_detail.cell(row=detail_row, column=4, value=time_out)
            ws_detail.cell(row=detail_row, column=5, value=method)
            ws_detail.cell(row=detail_row, column=6, value=status)
            detail_row += 1

        current_date += timedelta(days=1)

    # Auto-fit
    ws_detail.column_dimensions["A"].width = 10
    ws_detail.column_dimensions["B"].width = 25
    for col_letter in ["C", "D", "E", "F"]:
        ws_detail.column_dimensions[col_letter].width = 14

    # Save to bytes
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


# ------------------------------------------------------------------
# Custom Date Range Excel (Phase 5 — A2)
# ------------------------------------------------------------------

MAX_CUSTOM_RANGE_DAYS = 90


def generate_custom_range_excel(start_date: date, end_date: date) -> bytes:
    """Tạo Excel report cho khoảng ngày tùy chọn.

    Cùng format với generate_monthly_excel() nhưng nhận date range.

    Args:
        start_date: Ngày bắt đầu.
        end_date: Ngày kết thúc.

    Returns:
        bytes: Excel file content.

    Raises:
        ValueError: Nếu range > 90 ngày hoặc start > end.
    """
    if end_date < start_date:
        raise ValueError("end_date phải >= start_date")

    range_days = (end_date - start_date).days + 1
    if range_days > MAX_CUSTOM_RANGE_DAYS:
        raise ValueError(f"Max range is {MAX_CUSTOM_RANGE_DAYS} days")

    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill

    wb = Workbook()

    # ── Sheet 1: Tổng hợp ──
    ws_summary = wb.active
    ws_summary.title = "Tổng hợp"

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")

    headers = ["STT", "Họ tên", "Số ngày đi", "Muộn", "WFH", "Nghỉ phép", "Vắng"]
    for col_idx, header in enumerate(headers, 1):
        cell = ws_summary.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    # Dùng get_weekly_report_data với custom range
    weekly_data = get_weekly_report_data(start_date, end_date)

    row_idx = 2
    for stt, (uid, stats) in enumerate(weekly_data["summary"].items(), 1):
        ws_summary.cell(row=row_idx, column=1, value=stt)
        ws_summary.cell(row=row_idx, column=2, value=stats["name"])
        ws_summary.cell(row=row_idx, column=3, value=stats["present"])
        ws_summary.cell(row=row_idx, column=4, value=stats["late"])
        ws_summary.cell(row=row_idx, column=5, value=stats["wfh"])
        ws_summary.cell(row=row_idx, column=6, value=stats["on_leave"])
        ws_summary.cell(row=row_idx, column=7, value=stats["absent"])
        row_idx += 1

    ws_summary.column_dimensions["A"].width = 6
    ws_summary.column_dimensions["B"].width = 25
    for col_letter in ["C", "D", "E", "F", "G"]:
        ws_summary.column_dimensions[col_letter].width = 12

    # ── Sheet 2: Chi tiết ──
    ws_detail = wb.create_sheet("Chi tiết")

    detail_headers = ["Ngày", "Họ tên", "Giờ vào", "Giờ ra", "Phương thức", "Trạng thái"]
    for col_idx, header in enumerate(detail_headers, 1):
        cell = ws_detail.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    detail_row = 2
    current_date = start_date
    tz = get_tz()

    while current_date <= end_date:
        if current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            continue

        start_iso, end_iso = _date_range(current_date)

        checkins = db.select(
            "checkins",
            filters={
                "type": "in",
                "checked_at.gte": start_iso,
                "checked_at.lt": end_iso,
            },
            order="checked_at.asc",
        )

        checkouts = db.select(
            "checkins",
            filters={
                "type": "out",
                "checked_at.gte": start_iso,
                "checked_at.lt": end_iso,
            },
            order="checked_at.asc",
        )
        checkout_map = {co["user_id"]: co for co in checkouts}

        all_users = db.select("users", filters={"is_active": True})
        user_map = {u["id"]: u for u in all_users}

        checked_user_ids = set()
        for ci in checkins:
            uid = ci["user_id"]
            if uid in checked_user_ids:
                continue
            checked_user_ids.add(uid)

            user = user_map.get(uid)
            if not user:
                continue

            time_in = _format_checkin_time(ci["checked_at"])
            co = checkout_map.get(uid)
            time_out = _format_checkin_time(co["checked_at"]) if co else "—"
            method = ci.get("method", "")
            status = "Muộn" if _is_late(ci["checked_at"]) else "Đúng giờ"

            ws_detail.cell(row=detail_row, column=1, value=current_date.strftime("%d/%m"))
            ws_detail.cell(row=detail_row, column=2, value=user["full_name"])
            ws_detail.cell(row=detail_row, column=3, value=time_in)
            ws_detail.cell(row=detail_row, column=4, value=time_out)
            ws_detail.cell(row=detail_row, column=5, value=method)
            ws_detail.cell(row=detail_row, column=6, value=status)
            detail_row += 1

        current_date += timedelta(days=1)

    ws_detail.column_dimensions["A"].width = 10
    ws_detail.column_dimensions["B"].width = 25
    for col_letter in ["C", "D", "E", "F"]:
        ws_detail.column_dimensions[col_letter].width = 14

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()
