# Changelog — Pyng

> Tất cả thay đổi đáng chú ý được ghi lại ở đây.
> Format: [Conventional Commits](https://www.conventionalcommits.org/)

---

## [Unreleased]

### feat

- **Phase 2 — QR System** (Stream A):
  - `services/qr_service.py` — QR session CRUD, generate QR image (qrcode+Pillow), validate token, cleanup expired
  - `bot/handlers/qr_checkin.py` — QR check-in via deep link + manual input (/checkin_qr)
  - `api/qr/current.py` — GET /api/qr/current (JSON + base64 QR image)
  - `api/cron/qr_refresh.py` — Cron endpoint tạo QR mới mỗi 5 phút (giờ làm việc)
  - `qr/index.html` — QR display page: auto-fetch, countdown timer, deep link fallback
  - `bot/handlers/start.py` — Deep link routing: /start qr_TOKEN, /start nfc_TOKEN
  - `bot/handlers/admin.py` — /admin_qr: xem QR config, tạo QR mới
- **Phase 2 — NFC System** (Stream B):
  - `services/nfc_service.py` — NFC token CRUD, validate, list, deactivate
  - `bot/handlers/nfc_checkin.py` — NFC check-in via deep link (/start nfc_TOKEN)
  - `bot/handlers/admin.py` — /admin_nfc: tạo token, xem danh sách, vô hiệu hóa, hiển thị deep link
- **Phase 2 — Manual Fallback** (Stream C):
  - `bot/handlers/manual_checkin.py` — /manual check-in flow: lý do → selfie → pending admin
  - `bot/handlers/admin.py` — Manual approval: admin nhận ảnh + duyệt/từ chối inline buttons
  - `bot/handlers/checkin.py` — Re-export thêm QR + manual handlers
  - `bot/app.py` — Register QR, NFC, manual admin handlers

### fix

- **admin.py**: Fix `db.update()` gọi sai signature cho manual approval (P0)

- **Vercel deploy**: Bỏ `supabase` SDK — conflict httpx version với `python-telegram-bot`
  - Rewrite `db/client.py` → lightweight REST wrapper qua `httpx` (gọi PostgREST API trực tiếp)
  - Update `services/user_service.py`, `checkin_service.py`, `office_service.py` dùng REST client mới
  - Zero new dependencies — `httpx` đã có sẵn qua `python-telegram-bot`

### feat

- **Phase 1 — Wave 1**: Database & Services foundation
  - `db/client.py` — REST wrapper qua httpx (PostgREST API, service_role_key)
  - `services/user_service.py` — Register, activate, reject, is_admin
  - `services/checkin_service.py` — Checkin/checkout/WFH, working hours, duplicate check
  - `services/office_service.py` — Office CRUD, WiFi whitelist management
  - `bot/validators/gps_validator.py` — Geofence check (geopy), spoofing detection
  - `bot/validators/wifi_validator.py` — SSID whitelist validation
  - `requirements.txt` — Uncomment supabase, geopy
- **Phase 1 — Wave 2**: Bot Handlers (B1-B8)
  - `bot/handlers/start.py` — Registration flow (ConversationHandler: tên → email → chờ duyệt)
  - `bot/handlers/admin.py` — Admin approval (inline buttons), GPS settings, WiFi management
  - `bot/handlers/checkin.py` — GPS/WiFi check-in, checkout, WFH flow
  - `bot/app.py` — Register all handlers
  - `api/webhook.py` — Dùng create_bot() factory
- **Phase 1 — Wave 2**: Infra & Cron (C1-C3)
  - `api/cron/_helpers.py` — Shared cron utilities (auth, Telegram API via httpx)
  - `api/cron/morning.py` — Nhắc check-in 8:30 cho active users chưa check-in
  - `api/cron/evening.py` — Nhắc check-out 17:45 cho users đã check-in chưa checkout
  - `.github/workflows/cron-reminders.yml` — GitHub Actions cron (weekdays, UTC+7)

### refactor

- **Code review Phase 1**: Fix toàn bộ P1+P2+P3 issues
  - Tách `checkin.py` (423 dòng) thành 5 files: `gps_checkin.py`, `wifi_checkin.py`, `checkout.py`, `wfh.py`, `_helpers.py`
  - Sanitize error responses (không leak `str(e)` qua HTTP)
  - Tạo `config/timezone.py` — shared timezone helper (bỏ duplicate pattern)
  - Fix admin double `query.answer()`
  - Fix `OFFICE_WIFI_SSIDS` parsing edge case
  - Chuyển tất cả `print()` → `logging` module

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

### chore

- Sync 7 workflows từ templates → adapt cho Pyng tech stack
- Thêm mới: `docs-update.md`, `new-feature.md`
- Thêm 10 rule files (`.agents/rules/`) — adapt từ templates cho Pyng
- Thêm 2 skills: `writing-plans`, `brainstorming` — adapt từ superpowers
- Enforce commit body rule: BẮT BUỘC khi ≥3 files hoặc feat/chore

---

_Pyng — "Ping your presence" — BSMlabs Check-in Bot_
