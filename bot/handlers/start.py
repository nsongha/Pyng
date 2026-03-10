"""Handler cho lệnh /start — đăng ký nhân viên mới."""

from telegram import Update
from telegram.ext import ContextTypes


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý lệnh /start.

    Phase 0: Chào mừng + hiển thị thông tin cơ bản.
    Phase 1+: Sẽ thêm flow đăng ký (nhập tên, email, chờ admin duyệt).
    """
    user = update.effective_user

    welcome_text = (
        f"👋 Xin chào **{user.first_name}**!\n\n"
        f"Tôi là **PyngBot** — trợ lý chấm công BSMlabs.\n"
        f"_\"Ping your presence\"_ 📍\n\n"
        f"🔧 Bot đang trong giai đoạn phát triển.\n"
        f"Các tính năng sẽ sớm được cập nhật:\n"
        f"• ✅ Check-in/out bằng GPS, WiFi, QR, NFC\n"
        f"• 📊 Xem lịch sử & thống kê\n"
        f"• 🏠 Đăng ký WFH / Xin nghỉ phép\n"
        f"• 🏆 Gamification & Leaderboard\n\n"
        f"Telegram ID: `{user.id}`"
    )

    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
    )
