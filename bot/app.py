"""Pyng Bot — Application factory.

Tạo và cấu hình python-telegram-bot Application.
Dùng cho cả webhook (Vercel) và polling (local dev).
"""

from telegram.ext import Application

from config.settings import TELEGRAM_BOT_TOKEN
from bot.handlers.start import get_registration_handler
from bot.handlers.checkin import get_checkin_handlers
from bot.handlers.admin import (
    get_approval_handlers,
    get_admin_gps_handler,
    get_admin_wifi_handler,
    get_admin_qr_handler,
    get_admin_nfc_handler,
    get_manual_approval_handlers,
)
from bot.handlers.leave import (
    get_leave_request_handler,
    get_leave_approval_handlers,
    get_leave_balance_handler,
)
from bot.handlers.admin_panel import get_admin_panel_handlers
from bot.handlers.report import get_report_handlers


def create_bot() -> Application:
    """Tạo bot application với tất cả handlers.

    Handler order (python-telegram-bot groups):
    1. ConversationHandlers (registration, wifi checkin, wfh, admin GPS, admin WiFi)
    2. Command handlers (checkin, checkout)
    3. Message handlers (location)
    4. CallbackQuery handlers (admin approval)
    """
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # 1. Registration flow (ConversationHandler cho /start)
    app.add_handler(get_registration_handler())

    # 2. Check-in handlers (commands + location + wifi conversation + wfh conversation)
    for handler in get_checkin_handlers():
        app.add_handler(handler)

    # 3. Admin flows
    # Approval inline buttons
    for handler in get_approval_handlers():
        app.add_handler(handler)

    # Admin GPS settings (ConversationHandler)
    app.add_handler(get_admin_gps_handler())

    # Admin WiFi management (ConversationHandler)
    app.add_handler(get_admin_wifi_handler())

    # Admin QR config (ConversationHandler)
    app.add_handler(get_admin_qr_handler())

    # Admin NFC management (ConversationHandler)
    app.add_handler(get_admin_nfc_handler())

    # Manual check-in approval inline buttons
    for handler in get_manual_approval_handlers():
        app.add_handler(handler)

    # 4. Admin Panel (/admin — Phase 3)
    for handler in get_admin_panel_handlers():
        app.add_handler(handler)

    # 5. Leave management
    # Leave request conversation (/leave, /xinnghỉ)
    app.add_handler(get_leave_request_handler())

    # Leave approval inline buttons
    for handler in get_leave_approval_handlers():
        app.add_handler(handler)

    # Leave balance command (/phep)
    app.add_handler(get_leave_balance_handler())

    # 6. Report commands (/report, /baocao — Phase 3)
    for handler in get_report_handlers():
        app.add_handler(handler)

    return app
