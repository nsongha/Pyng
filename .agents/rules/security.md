---
description: Bảo mật cho Telegram bot, secrets management, input validation
---

# Security

## Secrets & Credentials

- Không hardcode secrets, API keys, credentials vào source code
- Sử dụng environment variables (`.env`)
- File `.env` phải nằm trong `.gitignore`
- Dùng `config/settings.py` để đọc env vars — KHÔNG dùng `os.environ` trực tiếp

## Telegram Bot Security

- Validate `telegram_id` cho mọi sensitive operation
- Admin commands: kiểm tra user có trong admin list
- Webhook endpoint: chỉ accept POST từ Telegram (validate source nếu cần)
- KHÔNG log sensitive data (token, passwords) — chỉ log user ID, action

## Input Validation

- Validate và sanitize mọi input từ user
- GPS coordinates: check range hợp lệ (-90/90, -180/180)
- Text input: strip, check length, escape special chars
- Callback data: validate format trước khi parse
- KHÔNG trust client data — luôn validate phía server

## Database Security

- Supabase RLS policies cho row-level access control
- Service role key: CHỈ dùng phía server, KHÔNG expose cho client
- Anon key: OK cho client-side (đã bị RLS restrict)
- Parameterized queries — KHÔNG concatenate SQL strings

## Proactive Alerts

- Nhắc nhở khi phát hiện potential security issue — dù không được hỏi
- Ví dụ: SQL injection risk, exposed tokens, missing auth check
