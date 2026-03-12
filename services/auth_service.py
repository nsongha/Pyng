"""Pyng — Auth Service cho Mini App API.

Validate Telegram WebApp initData bằng HMAC-SHA256.
Xem: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app

Flow:
    1. Parse initData query string → tách hash, sort params còn lại
    2. Secret key = HMAC-SHA256("WebAppData", BOT_TOKEN)
    3. Verify = HMAC-SHA256(secret_key, data_check_string) == hash
    4. Optional: check auth_date không quá MAX_AUTH_AGE_SECONDS
"""

import hashlib
import hmac
import json
import logging
import time
from functools import wraps
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, unquote

from config.settings import MINI_APP_URL, TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)

# initData hết hạn sau 24 giờ
# Lý do tăng từ 1h → 24h: Telegram client cache initData khi user mở app từ
# Recent Apps hoặc switch tabs. HMAC-SHA256 signature đủ bảo mật chống replay.
MAX_AUTH_AGE_SECONDS = 86400


# ------------------------------------------------------------------
# Core: Validate Telegram initData
# ------------------------------------------------------------------

def validate_telegram_init_data(init_data_str: str) -> tuple[bool, str]:
    """Validate Telegram WebApp initData bằng HMAC-SHA256.

    Args:
        init_data_str: Raw initData query string từ Telegram WebApp.

    Returns:
        tuple[bool, str]: (is_valid, error_reason).
            error_reason rỗng khi valid.
    """
    if not TELEGRAM_BOT_TOKEN:
        return False, "Bot token not configured"
    if not init_data_str:
        return False, "Missing auth header"

    try:
        # 1. Parse query string
        parsed = parse_qs(init_data_str, keep_blank_values=True)

        # 2. Extract hash
        received_hash = parsed.get("hash", [None])[0]
        if not received_hash:
            return False, "Missing hash in initData"

        # 3. Tạo data_check_string: sort params (trừ hash), join bằng \n
        data_pairs = []
        for key, values in parsed.items():
            if key == "hash":
                continue
            # parse_qs trả về list, lấy value đầu tiên
            data_pairs.append(f"{key}={values[0]}")

        data_pairs.sort()
        data_check_string = "\n".join(data_pairs)

        # 4. Tạo secret key: HMAC-SHA256("WebAppData", BOT_TOKEN)
        secret_key = hmac.new(
            b"WebAppData",
            TELEGRAM_BOT_TOKEN.encode("utf-8"),
            hashlib.sha256,
        ).digest()

        # 5. Tính hash: HMAC-SHA256(secret_key, data_check_string)
        computed_hash = hmac.new(
            secret_key,
            data_check_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # 6. So sánh (constant-time để tránh timing attack)
        if not hmac.compare_digest(computed_hash, received_hash):
            return False, "Invalid signature"

        # 7. Check auth_date không quá cũ
        auth_date_str = parsed.get("auth_date", [None])[0]
        if auth_date_str:
            auth_date = int(auth_date_str)
            if time.time() - auth_date > MAX_AUTH_AGE_SECONDS:
                logger.warning("initData expired: auth_date=%s", auth_date_str)
                return False, "Token expired"

        return True, ""

    except Exception:
        logger.exception("validate_telegram_init_data error")
        return False, "Validation error"


def parse_telegram_user(init_data_str: str) -> dict | None:
    """Extract user info từ Telegram initData.

    Args:
        init_data_str: Raw initData query string.

    Returns:
        dict | None: {id, username, first_name, auth_date} hoặc None.
    """
    if not init_data_str:
        return None

    try:
        parsed = parse_qs(init_data_str, keep_blank_values=True)

        # User data nằm trong param "user" dạng JSON string
        user_json = parsed.get("user", [None])[0]
        if not user_json:
            return None

        user_data = json.loads(unquote(user_json))
        auth_date = parsed.get("auth_date", [None])[0]

        return {
            "id": user_data.get("id"),
            "username": user_data.get("username"),
            "first_name": user_data.get("first_name"),
            "auth_date": int(auth_date) if auth_date else None,
        }

    except Exception:
        logger.exception("parse_telegram_user error")
        return None


# ------------------------------------------------------------------
# Decorator: require_auth
# ------------------------------------------------------------------

def require_auth(method):
    """Decorator cho Vercel serverless handler methods.

    Đọc header X-Telegram-Init-Data, validate, inject self._telegram_user.
    Return 401 với error reason cụ thể nếu invalid.

    Usage:
        class handler(BaseHTTPRequestHandler):
            @require_auth
            def do_GET(self):
                user = self._telegram_user  # {id, username, ...}
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        init_data = self.headers.get("X-Telegram-Init-Data", "")

        is_valid, error_reason = validate_telegram_init_data(init_data)
        if not is_valid:
            json_api_response(self, 401, {"ok": False, "error": error_reason})
            return

        telegram_user = parse_telegram_user(init_data)
        if not telegram_user or not telegram_user.get("id"):
            json_api_response(self, 401, {"ok": False, "error": "Invalid user data"})
            return

        # Inject user vào handler instance
        self._telegram_user = telegram_user
        return method(self, *args, **kwargs)

    return wrapper


# ------------------------------------------------------------------
# CORS Helper
# ------------------------------------------------------------------


def _get_cors_origin() -> str:
    """Trả về CORS origin: MINI_APP_URL nếu có, fallback '*' cho dev."""
    return MINI_APP_URL if MINI_APP_URL else "*"


# ------------------------------------------------------------------
# Response Helper
# ------------------------------------------------------------------

def json_api_response(
    handler: BaseHTTPRequestHandler,
    status: int,
    data: dict,
) -> None:
    """Gửi JSON response cho Mini App API.

    CORS headers được set ở vercel.json level (edge).
    Không set ở đây để tránh duplicate headers trong body.

    Args:
        handler: BaseHTTPRequestHandler instance.
        status: HTTP status code.
        data: Dict sẽ serialize thành JSON.
    """
    body = json.dumps(data, default=str, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.end_headers()
    handler.wfile.write(body)


def handle_cors_preflight(handler: BaseHTTPRequestHandler) -> None:
    """Handle CORS preflight request (OPTIONS).

    CORS headers được set ở vercel.json level (edge).
    Function chỉ trả 204 No Content.

    Args:
        handler: BaseHTTPRequestHandler instance.
    """
    handler.send_response(204)
    handler.end_headers()


def parse_request_body(handler: BaseHTTPRequestHandler) -> dict:
    """Parse JSON body từ POST request.

    Đọc Content-Length → self.rfile.read() → json.loads().

    Args:
        handler: BaseHTTPRequestHandler instance.

    Returns:
        dict: Parsed JSON body.

    Raises:
        ValueError: Nếu body rỗng hoặc không phải JSON hợp lệ.
    """
    content_length = int(handler.headers.get("Content-Length", 0))
    if content_length == 0:
        raise ValueError("Empty request body")

    raw_body = handler.rfile.read(content_length)
    if not raw_body:
        raise ValueError("Empty request body")

    try:
        return json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")
