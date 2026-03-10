# Changelog — Pyng

> Tất cả thay đổi đáng chú ý được ghi lại ở đây.
> Format: [Conventional Commits](https://www.conventionalcommits.org/)

---

## [Unreleased]

### docs

- Sửa ARCHITECTURE.md: sơ đồ kiến trúc Railway→Vercel, bỏ Redis & S3
- Sửa ARCHITECTURE.md: seed SQL giờ làm 08:30→08:45, 17:30→17:45
- Sửa ARCHITECTURE.md: QR diagram APScheduler→GitHub Actions Cron
- Sửa ARCHITECTURE.md: tách seed SQL → link tới DEPLOYMENT.md §4
- Sửa DEV_ROADMAP.md: Phase 0 bỏ Redis/Railway, đổi sang Vercel
- Sửa README.md: webhook URL railway→vercel, cập nhật folder structure
- Thống nhất QR expire = 5 phút ở PRD, BOT_FLOWS, USAGE, TECH_STACK
- Gộp APP_DESCRIPTION.md branding → PROJECT_CONTEXT.md (xóa file thừa)
- USAGE.md thêm cross-reference BOT_FLOWS.md
- Tạo CHANGELOG.md

### chore

- Tạo project scaffold: requirements.txt, .env.example, vercel.json, config/settings.py
- Tạo db/schema.sql (10 tables + indexes + RLS)
- Setup Supabase CLI + push migrations + seed data (BSMlabs config)
- Tạo GitHub repo nsongha/Pyng

### feat

- **Phase 0**: Bot webhook + /start command
  - `api/webhook.py` — Vercel serverless endpoint
  - `bot/app.py` — Application factory
  - `bot/handlers/start.py` — /start welcome message
  - Deploy: https://pyng.vercel.app
  - Bot: @pyng85111_bot

---

_Pyng — "Ping your presence" — BSMlabs Check-in Bot_
