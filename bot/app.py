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
)


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

    return app
