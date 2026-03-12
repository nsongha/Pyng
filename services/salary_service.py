"""Pyng — Salary Service.

Tính lương tháng cho nhân viên dựa trên dữ liệu check-in, OT, và nghỉ phép.

Công thức:
    net_salary = basic_salary + ot_allowance - late_deductions - unpaid_leave_deduction

Config keys (lưu trong system_config table):
    - salary_basic_monthly: Lương cơ bản/tháng (VND), default 10000000
    - salary_ot_rate_per_hour: OT rate/giờ (VND), default 50000
    - salary_late_deduction_per_min: Trừ lương/phút muộn (VND), default 5000
    - salary_late_grace_minutes: Grace period (phút), default 5

Dependencies:
    - services/config_service — đọc salary config
    - services/overtime_service — OT data
    - services/report_service — is_late() helper
    - services/leave_service — unpaid leave data
    - db/client — PostgREST queries
    - config/settings — WORK_START
"""

import logging
from datetime import date, datetime, timedelta

from db import client as db
from config.settings import WORK_START
from config.timezone import get_tz
from services.config_service import get_config
from services.overtime_service import get_monthly_overtime

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Defaults (nếu chưa set trong system_config)
# ------------------------------------------------------------------

DEFAULT_BASIC_MONTHLY = 10_000_000       # 10 triệu VND
DEFAULT_OT_RATE_PER_HOUR = 50_000        # 50k/giờ
DEFAULT_LATE_DEDUCTION_PER_MIN = 5_000   # 5k/phút
DEFAULT_LATE_GRACE_MINUTES = 5           # 5 phút (giống WORK_START grace)


# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------

def get_salary_config() -> dict:
    """Đọc salary config từ system_config table.

    Returns:
        dict: {
            "basic_monthly": int,
            "ot_rate_per_hour": int,
            "late_deduction_per_min": int,
            "late_grace_minutes": int,
        }
    """
    def _int(key: str, default: int) -> int:
        val = get_config(key)
        if val is None:
            return default
        try:
            return int(val)
        except (ValueError, TypeError):
            logger.warning("Invalid config value for %s: %s, using default %s", key, val, default)
            return default

    return {
        "basic_monthly": _int("salary_basic_monthly", DEFAULT_BASIC_MONTHLY),
        "ot_rate_per_hour": _int("salary_ot_rate_per_hour", DEFAULT_OT_RATE_PER_HOUR),
        "late_deduction_per_min": _int("salary_late_deduction_per_min", DEFAULT_LATE_DEDUCTION_PER_MIN),
        "late_grace_minutes": _int("salary_late_grace_minutes", DEFAULT_LATE_GRACE_MINUTES),
    }


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _count_working_days_in_month(month: int, year: int) -> int:
    """Đếm số ngày làm việc (Mon-Fri) trong tháng.

    Args:
        month: Tháng (1-12).
        year: Năm.

    Returns:
        int: Số ngày làm việc.
    """
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    count = 0
    current = first_day
    while current <= last_day:
        if current.weekday() < 5:  # Mon-Fri
            count += 1
        current += timedelta(days=1)
    return count


def _calculate_late_deductions(
    user_id: int,
    month: int,
    year: int,
    deduction_per_min: int,
    grace_minutes: int,
) -> dict:
    """Tính khấu trừ đi muộn trong tháng.

    Query check-ins (type='in', method != 'wfh') trong tháng.
    Mỗi check-in: tính late_minutes = checkin_minutes - (work_start_minutes + grace).
    Nếu late_minutes > 0 → cộng dồn deduction.

    Args:
        user_id: ID user.
        month: Tháng.
        year: Năm.
        deduction_per_min: Rate trừ lương/phút.
        grace_minutes: Grace period (phút).

    Returns:
        dict: {
            "late_count": int,
            "late_total_minutes": int,
            "late_deductions": int (VND),
        }
    """
    tz = get_tz()

    # Date range cho tháng
    start = datetime(year, month, 1, 0, 0, 0, tzinfo=tz)
    if month == 12:
        end = start.replace(year=year + 1, month=1)
    else:
        end = start.replace(month=month + 1)

    # Parse WORK_START thành minutes
    parts = WORK_START.split(":")
    work_start_minutes = int(parts[0]) * 60 + int(parts[1])
    threshold_minutes = work_start_minutes + grace_minutes

    # Query check-ins (type='in') trong tháng
    checkins = db.select(
        "checkins",
        columns="id,method,checked_at",
        filters={
            "user_id": user_id,
            "type": "in",
            "checked_at.gte": start.isoformat(),
            "checked_at.lt": end.isoformat(),
        },
    )

    late_count = 0
    late_total_minutes = 0

    for ci in checkins:
        # WFH không tính muộn
        if ci.get("method") == "wfh":
            continue

        checked_at_str = ci.get("checked_at")
        if not checked_at_str:
            continue

        checked_at = datetime.fromisoformat(checked_at_str)
        if checked_at.tzinfo is None:
            checked_at = checked_at.replace(tzinfo=tz)

        checkin_minutes = checked_at.hour * 60 + checked_at.minute

        if checkin_minutes > threshold_minutes:
            late_mins = checkin_minutes - threshold_minutes
            late_count += 1
            late_total_minutes += late_mins

    return {
        "late_count": late_count,
        "late_total_minutes": late_total_minutes,
        "late_deductions": late_total_minutes * deduction_per_min,
    }


def _calculate_unpaid_leave_deduction(
    user_id: int,
    month: int,
    year: int,
    daily_rate: int,
) -> dict:
    """Tính khấu trừ nghỉ không lương trong tháng.

    Query leaves: user_id, leave_type='unpaid', status='approved', start_date trong tháng.

    Args:
        user_id: ID user.
        month: Tháng.
        year: Năm.
        daily_rate: Lương/ngày (basic_salary / working_days).

    Returns:
        dict: {
            "unpaid_leave_days": float,
            "unpaid_leave_deduction": int (VND),
        }
    """
    start_str = f"{year}-{month:02d}-01"
    if month == 12:
        end_str = f"{year + 1}-01-01"
    else:
        end_str = f"{year}-{month + 1:02d}-01"

    unpaid_leaves = db.select(
        "leaves",
        columns="days_count",
        filters={
            "user_id": user_id,
            "leave_type": "unpaid",
            "status": "approved",
            "start_date.gte": start_str,
            "start_date.lt": end_str,
        },
    )

    unpaid_days = sum(float(leave.get("days_count", 0)) for leave in unpaid_leaves)

    return {
        "unpaid_leave_days": unpaid_days,
        "unpaid_leave_deduction": int(unpaid_days * daily_rate),
    }


# ------------------------------------------------------------------
# Core: Calculate Monthly Salary
# ------------------------------------------------------------------

def calculate_monthly_salary(user_id: int, month: int, year: int) -> dict:
    """Tính lương tháng cho 1 user.

    Công thức: net = basic + OT - late_deductions - unpaid_leave_deduction

    Args:
        user_id: ID user trong bảng users.
        month: Tháng (1-12).
        year: Năm.

    Returns:
        dict: {
            "basic_salary": int,
            "ot_minutes": int,
            "ot_allowance": int,
            "late_count": int,
            "late_total_minutes": int,
            "late_deductions": int,
            "unpaid_leave_days": float,
            "unpaid_leave_deduction": int,
            "net_salary": int,
            "working_days": int,
            "status": str — "estimated" (luôn, vì chưa có payroll cycle)
        }
    """
    config = get_salary_config()

    # 1. Basic salary
    basic_salary = config["basic_monthly"]

    # 2. Working days
    working_days = _count_working_days_in_month(month, year)
    daily_rate = basic_salary // working_days if working_days > 0 else 0

    # 3. OT allowance (reuse overtime_service)
    ot_data = get_monthly_overtime(user_id, month, year)
    ot_minutes = ot_data["total_minutes"]
    ot_hours = ot_minutes / 60
    ot_allowance = int(ot_hours * config["ot_rate_per_hour"])

    # 4. Late deductions
    late_data = _calculate_late_deductions(
        user_id, month, year,
        config["late_deduction_per_min"],
        config["late_grace_minutes"],
    )

    # 5. Unpaid leave deduction
    unpaid_data = _calculate_unpaid_leave_deduction(
        user_id, month, year, daily_rate,
    )

    # 6. Net salary
    net_salary = (
        basic_salary
        + ot_allowance
        - late_data["late_deductions"]
        - unpaid_data["unpaid_leave_deduction"]
    )

    return {
        "basic_salary": basic_salary,
        "ot_minutes": ot_minutes,
        "ot_allowance": ot_allowance,
        "late_count": late_data["late_count"],
        "late_total_minutes": late_data["late_total_minutes"],
        "late_deductions": late_data["late_deductions"],
        "unpaid_leave_days": unpaid_data["unpaid_leave_days"],
        "unpaid_leave_deduction": unpaid_data["unpaid_leave_deduction"],
        "net_salary": max(0, net_salary),
        "working_days": working_days,
        "status": "estimated",
    }


# ------------------------------------------------------------------
# Salary Report (all users)
# ------------------------------------------------------------------

def get_salary_report(month: int, year: int) -> dict:
    """Tổng hợp lương toàn bộ nhân viên trong tháng.

    Args:
        month: Tháng (1-12).
        year: Năm.

    Returns:
        dict: {
            "month": int,
            "year": int,
            "working_days": int,
            "users": list[dict] — [{user_id, full_name, ...salary_breakdown}],
            "grand_total": int (tổng net_salary),
        }
    """
    all_users = db.select("users", filters={"is_active": True})
    working_days = _count_working_days_in_month(month, year)

    users_salary = []
    grand_total = 0

    for user in all_users:
        salary = calculate_monthly_salary(user["id"], month, year)
        users_salary.append({
            "user_id": user["id"],
            "full_name": user.get("full_name", ""),
            **salary,
        })
        grand_total += salary["net_salary"]

    return {
        "month": month,
        "year": year,
        "working_days": working_days,
        "users": users_salary,
        "grand_total": grand_total,
    }
