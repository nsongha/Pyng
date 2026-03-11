"""Pyng — Mood Handlers.

B1: Mood prompt sau check-in — inline keyboard hỏi cảm xúc.
B5: Burnout alert — cảnh báo admin khi user SOS 3 ngày liên tiếp.

Callback data prefix: "mood_" cho mood buttons, "gami_burnout_" cho burnout actions.
"""

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

from services.mood_service import (
    record_mood,
    check_burnout_alert,
    MOOD_LABELS,
    POSITIVE_MOODS,
    MOOD_BONUS_POINTS,
)
from bot.handlers._helpers import get_active_user_or_none
from config.settings import ADMIN_TELEGRAM_IDS

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# B1: Mood Prompt sau check-in
# ------------------------------------------------------------------

# Mapping mood type → callback data key
MOOD_CHOICES = [
    ("great", "🔥 Siêu năng suất"),
    ("good", "😊 Bình thường"),
    ("tired", "😴 Hơi mệt"),
    ("sos", "🆘 Cần hỗ trợ"),
]


async def send_mood_prompt(
    chat_id: int,
    checkin_id: int,
    user_id: int,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Gửi inline keyboard hỏi mood sau check-in sáng.

    Chỉ gọi khi check-in sáng (type='in'), KHÔNG gọi khi checkout/WFH.
    Callback data format: mood_TYPE_CHECKINID (vd: mood_great_42).

    Args:
        chat_id: Telegram chat ID để gửi message.
        checkin_id: ID checkin record trong DB.
        user_id: ID user trong bảng users.
        context: Telegram bot context.
    """
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔥 Siêu năng suất",
                callback_data=f"mood_great_{checkin_id}",
            ),
            InlineKeyboardButton(
                "😊 Bình thường",
                callback_data=f"mood_good_{checkin_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                "😴 Hơi mệt",
                callback_data=f"mood_tired_{checkin_id}",
            ),
            InlineKeyboardButton(
                "🆘 Cần hỗ trợ",
                callback_data=f"mood_sos_{checkin_id}",
            ),
        ],
    ])

    await context.bot.send_message(
        chat_id=chat_id,
        text="Hôm nay bạn cảm thấy thế nào? 💭",
        reply_markup=keyboard,
    )


async def handle_mood_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Xử lý khi user bấm mood button.

    Parse callback data: mood_TYPE_CHECKINID → gọi record_mood().
    Nếu mood SOS → kiểm tra burnout alert (B5).
    """
    query = update.callback_query
    await query.answer()

    # Parse: "mood_great_42" → mood_type="great", checkin_id=42
    parts = query.data.split("_")
    if len(parts) != 3:
        logger.warning("Invalid mood callback data: %s", query.data)
        return

    _, mood_type, checkin_id_str = parts

    try:
        checkin_id = int(checkin_id_str)
    except ValueError:
        logger.warning("Invalid checkin_id in mood callback: %s", checkin_id_str)
        return

    # Validate mood type
    valid_moods = {m[0] for m in MOOD_CHOICES}
    if mood_type not in valid_moods:
        logger.warning("Invalid mood type: %s", mood_type)
        return

    # Lấy user
    user = get_active_user_or_none(query.from_user.id)
    if not user:
        await query.edit_message_text("❌ Không tìm thấy tài khoản của bạn.")
        return

    # Ghi mood vào DB
    record_mood(user["id"], checkin_id, mood_type)

    # Tạo response message
    mood_label = MOOD_LABELS.get(mood_type, mood_type)
    response = f"Cảm ơn bạn! {mood_label}"

    if mood_type in POSITIVE_MOODS:
        response += f"\n🎁 +{MOOD_BONUS_POINTS} pts (mood bonus)"

    await query.edit_message_text(response)

    # B5: Kiểm tra burnout nếu mood là SOS
    if mood_type == "sos":
        user_name = user.get("full_name", "Unknown")
        await check_and_send_burnout_alert(
            user_id=user["id"],
            user_name=user_name,
            telegram_id=query.from_user.id,
            context=context,
        )


# ------------------------------------------------------------------
# B5: Burnout Alert cho Manager/Admin
# ------------------------------------------------------------------


async def check_and_send_burnout_alert(
    user_id: int,
    user_name: str,
    telegram_id: int,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Kiểm tra burnout và gửi cảnh báo cho admin nếu phát hiện.

    Gọi mood_service.check_burnout_alert() — nếu True (3 ngày SOS liên tiếp),
    gửi cảnh báo private cho tất cả admin trong ADMIN_TELEGRAM_IDS.

    Args:
        user_id: ID user trong bảng users.
        user_name: Tên đầy đủ của user.
        telegram_id: Telegram ID của user (để admin nhắn tin).
        context: Telegram bot context.
    """
    is_burnout = check_burnout_alert(user_id)
    if not is_burnout:
        return

    logger.warning("Burnout alert triggered for user %s (%s)", user_name, user_id)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💬 Nhắn tin ngay",
                url=f"tg://user?id={telegram_id}",
            ),
            InlineKeyboardButton(
                "Bỏ qua",
                callback_data=f"gami_burnout_dismiss_{user_id}",
            ),
        ],
    ])

    alert_text = (
        f"⚠️ **Cảnh báo Burnout**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 {user_name} đã báo cáo \"🆘 Cần hỗ trợ\"\n"
        f"**3 ngày liên tiếp**.\n\n"
        f"Bạn có muốn liên hệ với họ không?"
    )

    for admin_id in ADMIN_TELEGRAM_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=alert_text,
                parse_mode="Markdown",
                reply_markup=keyboard,
            )
        except Exception as e:
            logger.error(
                "Failed to send burnout alert to admin %s: %s", admin_id, e
            )


async def handle_burnout_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Xử lý khi admin bấm nút Bỏ qua trên burnout alert.

    Nút "Nhắn tin ngay" dùng url→ tg://user nên không cần handler.
    Chỉ cần handler cho "Bỏ qua" (dismiss).
    """
    query = update.callback_query
    await query.answer()

    # Parse: "gami_burnout_dismiss_42" → user_id=42
    await query.edit_message_text(
        (query.message.text or "") + "\n\n✅ Đã ghi nhận.",
    )


# ------------------------------------------------------------------
# Handler factories
# ------------------------------------------------------------------


def get_mood_handlers() -> list:
    """Trả về mood + burnout handlers.

    Returns:
        list: [CallbackQueryHandler mood, CallbackQueryHandler burnout_dismiss].
    """
    return [
        CallbackQueryHandler(handle_mood_callback, pattern=r"^mood_(great|good|tired|sos)_\d+$"),
        CallbackQueryHandler(handle_burnout_callback, pattern=r"^gami_burnout_dismiss_\d+$"),
    ]
