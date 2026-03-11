---
description: Bảo mật cơ bản, secrets management, input validation
---

# Security

## Secrets & Credentials

- Không hardcode secrets, API keys, credentials vào source code
- Sử dụng environment variables (`.env`, `.env.local`)
- File `.env` phải nằm trong `.gitignore`

## Secrets Management

- **Env audit**: verify `.env.example` sync với env thật khi thêm/xóa env var
- **Rotation**:
  - Renew `TELEGRAM_BOT_TOKEN` nếu nghi bị leak (BotFather → Revoke)
  - Renew `SUPABASE_SERVICE_ROLE_KEY` nếu nghi bị lộ (Supabase Dashboard)
  - Renew `CRON_SECRET` + `JWT_SECRET` yearly hoặc khi team member rời
- **Team member rời**: revoke access Vercel, GitHub, Supabase. Rotate shared secrets
- **Checklist khi deploy**, verify tất cả required env vars:
  - `TELEGRAM_BOT_TOKEN`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
  - `CRON_SECRET`, `JWT_SECRET`, `ADMIN_TELEGRAM_IDS`

## Input Validation

- Validate và sanitize mọi input từ user hoặc external source
- Không trust client-side validation — luôn validate phía server

## Proactive Alerts

- Nhắc nhở khi phát hiện potential security issue — dù không được hỏi
- Ví dụ: SQL injection risk, XSS vulnerability, exposed sensitive data
