"""Vercel Serverless Function — /api/leave.

Router cho leave endpoints:
    - GET  /api/leave/my       → Danh sách leave + balance
    - POST /api/leave/request  → Tạo đơn xin nghỉ
    - OPTIONS                  → CORS preflight

Gộp từ leave/my.py + leave/request.py để giảm function count (Vercel Hobby limit 12).
"""

import logging
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from services.auth_service import (
    require_auth,
    json_api_response,
    handle_cors_preflight,
    parse_request_body,
)
from services.user_service import get_by_telegram_id
from services.leave_service import (
    create_leave_request,
    get_user_leaves,
    get_remaining_leave_days,
)
from db import client as db
from config.settings import ADMIN_GROUP_ID, TELEGRAM_BOT_TOKEN
from config.timezone import get_tz

logger = logging.getLogger(__name__)

# --- Constants ---

VALID_LEAVE_TYPES = {"annual", "sick", "compensatory", "unpaid"}

LEAVE_TYPE_LABELS = {
    "annual": "Phép năm",
    "sick": "Nghỉ ốm",
    "compensatory": "Nghỉ bù",
    "unpaid": "Không lương",
}


# --- Helpers ---

def _validate_leave_request(body: dict, user_id: int) -> tuple[bool, str]:
    """Validate leave request body.

    Args:
        body: Request body dict.
        user_id: ID user.

    Returns:
        tuple: (is_valid, error_message)
    """
    leave_type = body.get("leave_type")
    start_date_str = body.get("start_date")
    end_date_str = body.get("end_date")

    if not leave_type or not start_date_str or not end_date_str:
        return False, "Thiếu trường bắt buộc: leave_type, start_date, end_date"

    if leave_type not in VALID_LEAVE_TYPES:
        return False, f"leave_type không hợp lệ. Chấp nhận: {', '.join(VALID_LEAVE_TYPES)}"

    try:
        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)
    except ValueError:
        return False, "Định dạng ngày không hợp lệ. Dùng YYYY-MM-DD"

    if end_date < start_date:
        return False, "end_date phải >= start_date"

    existing = get_user_leaves(user_id)
    for leave in existing:
        if leave.get("status") == "rejected":
            continue
        ex_start = date.fromisoformat(leave["start_date"])
        ex_end = date.fromisoformat(leave["end_date"])
        if start_date <= ex_end and end_date >= ex_start:
            return False, f"Trùng ngày với đơn nghỉ #{leave['id']} ({leave['start_date']} → {leave['end_date']})"

    return True, ""


def _notify_admin_leave_request(user_name: str, leave_type: str, start_date: str, end_date: str, reason: str | None) -> None:
    """Gửi notification cho admin group về leave request mới."""
    if not ADMIN_GROUP_ID or not TELEGRAM_BOT_TOKEN:
        return

    import httpx

    label = LEAVE_TYPE_LABELS.get(leave_type, leave_type)
    reason_text = f"\n📝 Lý do: {reason}" if reason else ""

    text = (
        f"📋 *Đơn nghỉ mới (Mini App)*\n\n"
        f"👤 {user_name}\n"
        f"📂 Loại: {label}\n"
        f"📅 Từ: {start_date} → {end_date}\n"
        f"{reason_text}\n\n"
        f"Duyệt trong bot: /phep"
    )

    try:
        api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        httpx.post(api_url, json={
            "chat_id": ADMIN_GROUP_ID,
            "text": text,
            "parse_mode": "Markdown",
        }, timeout=10)
    except Exception as e:
        logger.warning("Failed to notify admin group about leave request: %s", e)


def _handle_get_my_leaves(handler_self) -> None:
    """GET /api/leave/my — Danh sách leaves + balance."""
    try:
        telegram_id = handler_self._telegram_user["id"]

        user = get_by_telegram_id(telegram_id)
        if not user:
            json_api_response(handler_self, 404, {"error": "User not found"})
            return

        parsed_url = urlparse(handler_self.path)
        params = parse_qs(parsed_url.query)
        year_str = params.get("year", [None])[0]

        tz = get_tz()
        now = datetime.now(tz)

        if year_str:
            try:
                year = int(year_str)
            except ValueError:
                json_api_response(handler_self, 400, {"error": "Invalid year format"})
                return
        else:
            year = now.year

        leaves = get_user_leaves(user["id"], year=year)
        balance = get_remaining_leave_days(user["id"])

        json_api_response(handler_self, 200, {
            "ok": True,
            "year": year,
            "leaves": leaves,
            "balance": balance,
        })

    except Exception:
        logger.exception("GET /api/leave/my error")
        json_api_response(handler_self, 500, {"ok": False, "error": "Internal error"})


def _handle_post_leave_request(handler_self) -> None:
    """POST /api/leave/request — Tạo leave request mới."""
    try:
        telegram_id = handler_self._telegram_user["id"]

        user = get_by_telegram_id(telegram_id)
        if not user:
            json_api_response(handler_self, 404, {"error": "User not found"})
            return

        try:
            body = parse_request_body(handler_self)
        except ValueError as e:
            json_api_response(handler_self, 400, {"error": str(e)})
            return

        is_valid, error_msg = _validate_leave_request(body, user["id"])
        if not is_valid:
            json_api_response(handler_self, 409, {"error": error_msg})
            return

        start_date = date.fromisoformat(body["start_date"])
        end_date = date.fromisoformat(body["end_date"])

        leave = create_leave_request(
            user_id=user["id"],
            leave_type=body["leave_type"],
            start_date=start_date,
            end_date=end_date,
            reason=body.get("reason"),
        )

        _notify_admin_leave_request(
            user.get("full_name", ""),
            body["leave_type"],
            body["start_date"],
            body["end_date"],
            body.get("reason"),
        )

        json_api_response(handler_self, 201, {
            "ok": True,
            "leave": leave,
        })

    except Exception:
        logger.exception("POST /api/leave/request error")
        json_api_response(handler_self, 500, {"ok": False, "error": "Internal error"})


# --- Vercel Handler ---

class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler — /api/leave router.

    Routes:
        GET  /api/leave/my       → _handle_get_my_leaves
        POST /api/leave/request  → _handle_post_leave_request
    """

    @require_auth
    def do_GET(self):
        """Route GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path.endswith("/leave/my") or path.endswith("/leave"):
            _handle_get_my_leaves(self)
        else:
            json_api_response(self, 404, {"error": "Not found"})

    @require_auth
    def do_POST(self):
        """Route POST requests."""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path.endswith("/leave/request"):
            _handle_post_leave_request(self)
        else:
            json_api_response(self, 404, {"error": "Not found"})

    def do_OPTIONS(self):
        """CORS preflight."""
        handle_cors_preflight(self)
