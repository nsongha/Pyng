"""Vercel Serverless Function — QR Current.

Endpoint: GET /api/qr/current
Trả về QR code hiện tại (active, chưa expired) dưới dạng JSON.

Response format:
{
    "token": "A1B2C3D4",
    "expire_at": "2026-03-11T09:00:00+07:00",
    "deep_link_url": "https://t.me/PyngBot?start=qr_A1B2C3D4",
    "qr_image_base64": "iVBORw0KGgo..."
}
"""

import base64
import json
import logging
from http.server import BaseHTTPRequestHandler

logger = logging.getLogger(__name__)

from services.qr_service import get_current_qr, generate_qr_image, _build_deep_link
from services.office_service import get_active_office


def _json_response(handler: BaseHTTPRequestHandler, status: int, data: dict) -> None:
    """Gửi JSON response.

    Args:
        handler: HTTP handler instance.
        status: HTTP status code.
        data: Response data.
    """
    body = json.dumps(data, default=str).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
    handler.end_headers()
    handler.wfile.write(body)


class handler(BaseHTTPRequestHandler):
    """Vercel serverless handler — GET /api/qr/current."""

    def do_GET(self):
        """Trả về QR code hiện tại."""
        try:
            office = get_active_office()
            if not office:
                _json_response(self, 404, {
                    "error": "Chưa có office nào được cấu hình.",
                })
                return

            # Lấy hoặc tạo QR session
            qr_session = get_current_qr(office["id"])

            # Generate deep link và QR image
            deep_link_url = _build_deep_link(qr_session["token"])
            qr_image_bytes = generate_qr_image(deep_link_url)
            qr_image_base64 = base64.b64encode(qr_image_bytes).decode()

            _json_response(self, 200, {
                "ok": True,
                "token": qr_session["token"],
                "expire_at": qr_session["expire_at"],
                "deep_link_url": deep_link_url,
                "qr_image_base64": qr_image_base64,
            })

        except Exception as e:
            logger.exception("QR current error")
            _json_response(self, 500, {"ok": False, "error": "Internal error"})

    def do_OPTIONS(self):
        """CORS preflight."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
