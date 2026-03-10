---
description: Error handling cho Telegram bot và Vercel serverless
---

# Error Handling

## Telegram Bot

- LUÔN try/except trong handler — bot KHÔNG ĐƯỢC crash vì 1 user
- Trả message thân thiện bằng tiếng Việt khi có lỗi
- Log error đầy đủ (type, message, traceback) cho debugging

```python
async def checkin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = await checkin_service.process(update.effective_user.id)
        await update.message.reply_text(result.message)
    except ValidationError as e:
        await update.message.reply_text(f"⚠️ {e.user_message}")
    except Exception as e:
        print(f"[Error] checkin: {type(e).__name__}: {e}")
        await update.message.reply_text(
            "❌ Có lỗi xảy ra, vui lòng thử lại sau."
        )
```

## Vercel Serverless

- LUÔN trả HTTP 200 cho Telegram webhook (tránh retry loop)
- Log error chi tiết nhưng KHÔNG expose cho user
- Trả JSON response với `{"ok": false, "error": "..."}` cho internal errors

## Database (Supabase)

- Handle connection errors gracefully
- Retry logic cho transient failures
- KHÔNG expose SQL errors cho end user

## Error Message Guidelines

- Ngắn gọn, thân thiện, bằng tiếng Việt
- Dùng emoji để dễ nhận biết: ❌ lỗi, ⚠️ cảnh báo, ✅ thành công
- Gợi ý hành động tiếp theo: "Vui lòng thử lại" hoặc "Liên hệ admin"
