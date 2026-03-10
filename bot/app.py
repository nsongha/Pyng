"""Pyng Bot — Application factory.

Tạo và cấu hình python-telegram-bot Application.
Dùng cho cả webhook (Vercel) và polling (local dev).
"""

from telegram.ext import Application, CommandHandler

from config.settings import TELEGRAM_BOT_TOKEN
from bot.handlers.start import start_command


def create_bot() -> Application:
    """Tạo bot application với tất cả handlers."""
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start_command))

    return app
