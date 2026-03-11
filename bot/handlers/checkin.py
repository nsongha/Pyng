"""Pyng — Check-in Handlers (re-export module).

Module này tập hợp tất cả check-in related handlers.
Từng mode đã tách riêng file để dễ bảo trì:
- gps_checkin.py — GPS check-in (/checkin + location)
- wifi_checkin.py — WiFi check-in (/checkin_wifi)
- qr_checkin.py — QR check-in (/checkin_qr + deep link)
- manual_checkin.py — Manual check-in (/manual, /checkin_manual + selfie)
- nfc_checkin.py — NFC check-in (deep link via start.py, không có command riêng)
- checkout.py — Check-out (/checkout)
- wfh.py — WFH (/wfh)
"""

from bot.handlers.gps_checkin import get_gps_checkin_handlers
from bot.handlers.wifi_checkin import get_wifi_checkin_handler
from bot.handlers.qr_checkin import get_qr_checkin_handler
from bot.handlers.manual_checkin import get_manual_checkin_handler
from bot.handlers.checkout import get_checkout_handler
from bot.handlers.wfh import get_wfh_handler


def get_checkin_handlers() -> list:
    """Trả về tất cả checkin-related handlers.

    Returns:
        list: All handlers for check-in (GPS, WiFi, QR, Manual), checkout, WFH.
    """
    return [
        *get_gps_checkin_handlers(),
        get_wifi_checkin_handler(),
        get_qr_checkin_handler(),
        get_manual_checkin_handler(),
        get_checkout_handler(),
        get_wfh_handler(),
    ]
