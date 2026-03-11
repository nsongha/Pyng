"""Vercel Serverless Function — POST /api/leave/request.

Endpoint: POST /api/leave/request
Auth: Telegram initData (X-Telegram-Init-Data header)

Tạo leave request mới (qua leave_service có sẵn).
Gửi notification cho admin group qua Telegram Bot API.
"""

import logging
from datetime import date
from http.server import BaseHTTPRequestHandler

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

logger = logging.getLogger(__name__)

# Leave types hợp lệ
VALID_LEAVE_TYPES = {"annual", "sick", "compensatory", "unpaid"}

# Vietnamese labels cho leave types
LEAVE_TYPE_LABELS = {
    "annual": "Phép năm",
    "sick": "Nghỉ ốm",
    "compensatory": "Nghỉ bù",
    "unpaid": "Không lương",
}


def _validate_leave_request(body: dict, user_id: int) -> tuple[bool, str]:
    """Validate leave request body.

    Args:
        body: Request body dict.
        user_id: ID user.

    Returns:
        tuple: (is_valid, error_message)
    """
    # Required fields
    leave_type = body.get("leave_type")
    start_date_str = body.get("start_date")
    end_date_str = body.get("end_date")

    if not leave_type or not start_date_str or not end_date_str:
        return False, "Thiếu trường bắt buộc: leave_type, start_date, end_date"

    if leave_type not in VALID_LEAVE_TYPES:
        return False, f"leave_type không hợp lệ. Chấp nhận: {', '.join(VALID_LEAVE_TYPES)}"

    # Parse dates
    try:
        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)
    except ValueError:
        return False, "Định dạng ngày không hợp lệ. Dùng YYYY-MM-DD"

    if end_date < start_date:
        return False, "end_date phải >= start_date"

    # Check overlap với leave đã có
    existing = get_user_leaves(user_id)
    for leave in existing:
        if leave.get("status") == "rejected":
            continue
        ex_start = date.fromisoformat(leave["start_date"])
        ex_end = date.fromisoformat(leave["end_date"])
        # Overlap nếu: start <= ex_end AND end >= ex_start
        if start_date <= ex_end and end_date >= ex_start:
            return False, f"Trùng ngày với đơn nghỉ #{leave['id']} ({leave['start_date']} → {leave['end_date']})"

    return True, ""


async def _notify_admin_leave_request(user_name: str, leave_type: str, start_date: str, end_date: str, reason: str | None) -> None:
    """Gửi notification cho admin group về leave request mới.

    Args:
        user_name: Tên nhân viên.
        leave_type: Loại nghỉ.
        start_date: Ngày bắt đầu.
        end_date: Ngày kết thúc.
        reason: Lý do.
    """
    if not ADMIN_GROUP_ID or not TELEGRAM_BOT_TOKEN:
        return

    from services.cron_helpers import send_telegram_message

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
        await send_telegram_message(ADMIN_GROUP_ID, text)
    except Exception as e:
        logger.warning("Failed to notify admin group about leave request: %s", e)


class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler — POST /api/leave/request."""

    @require_auth
    def do_POST(self):
        """Tạo leave request mới."""
        try:
            telegram_id = self._telegram_user["id"]

            user = get_by_telegram_id(telegram_id)
            if not user:
                json_api_response(self, 404, {"error": "User not found"})
                return

            # Parse body
            try:
                body = parse_request_body(self)
            except ValueError as e:
                json_api_response(self, 400, {"error": str(e)})
                return

            # Validate
            is_valid, error_msg = _validate_leave_request(body, user["id"])
            if not is_valid:
                json_api_response(self, 409, {"error": error_msg})
                return

            # Parse dates
            start_date = date.fromisoformat(body["start_date"])
            end_date = date.fromisoformat(body["end_date"])

            # Create leave request
            leave = create_leave_request(
                user_id=user["id"],
                leave_type=body["leave_type"],
                start_date=start_date,
                end_date=end_date,
                reason=body.get("reason"),
            )

            # Notify admin (async, fire-and-forget)
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(_notify_admin_leave_request(
                        user.get("full_name", ""),
                        body["leave_type"],
                        body["start_date"],
                        body["end_date"],
                        body.get("reason"),
                    ))
                else:
                    asyncio.run(_notify_admin_leave_request(
                        user.get("full_name", ""),
                        body["leave_type"],
                        body["start_date"],
                        body["end_date"],
                        body.get("reason"),
                    ))
            except Exception:
                logger.warning("Failed to send admin notification for leave request")

            json_api_response(self, 201, {
                "ok": True,
                "leave": leave,
            })

        except Exception:
            logger.exception("POST /api/leave/request error")
            json_api_response(self, 500, {"ok": False, "error": "Internal error"})

    def do_OPTIONS(self):
        """CORS preflight."""
        handle_cors_preflight(self)
