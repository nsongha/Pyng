# Changelog — Pyng

> Tất cả thay đổi đáng chú ý được ghi lại ở đây.
> Format: [Conventional Commits](https://www.conventionalcommits.org/)

---

## [Unreleased]

### fix

- **Phase 6 — Stabilize & Fix API** (Stream A):
  - `services/auth_service.py` — Bỏ CORS headers khỏi Python function body (fix JSON parse error trên Vercel)
  - `services/auth_service.py` — Tăng `MAX_AUTH_AGE_SECONDS` 3600→86400 (fix Token expired)
  - `api/me.py`, `api/checkins.py` — Bỏ query column `is_ontime` (không tồn tại trong DB)
  - `vercel.json` — Chuyển CORS headers sang edge config, bỏ CSP `default-src 'self'`

### feat

- **Phase 5 — Backend Enhancement** (Stream A):
  - `services/overtime_service.py` — Overtime tracking: 30 phút grace sau WORK_END, cap 4h/ngày
  - `services/report_service.py` — Custom date range Excel export (max 90 ngày)
  - `bot/handlers/report.py` — `/report YYYY-MM-DD YYYY-MM-DD` custom range command
  - `bot/handlers/admin.py` — Bulk approve manual check-ins (inline button `bulk_approve_all`)
  - `bot/app.py` — Register `get_bulk_approve_handlers()`

- **Phase 5 — Mini App Charts** (Stream B):
  - `api/checkins/chart.py` — GET `/api/checkins/chart` (daily hours, summary, trend)
  - `api/overtime.py` — GET `/api/overtime` (monthly OT data)
  - `miniapp/src/pages/Charts.tsx` — Month selector + stats + trend display
  - `miniapp/src/components/charts/WorkingHoursChart.tsx` — Recharts bar chart
  - `miniapp/src/components/charts/AttendanceDonut.tsx` — Donut chart
  - `miniapp/src/components/OvertimeCard.tsx` — OT summary + sparkline

- **Phase 5 — Mini App Leave Form** (Stream C):
  - `api/leave/request.py` — POST `/api/leave/request` + admin notification
  - `api/leave/my.py` — GET `/api/leave/my` (leave list + balance)
  - `miniapp/src/pages/Leave.tsx` — Tab toggle (list/form) + balance card
  - `miniapp/src/components/LeaveForm.tsx` — Date picker + validation + haptic
  - `miniapp/src/components/LeaveList.tsx` — Status badges + pull-to-refresh
  - `miniapp/src/App.tsx` — React Router + BottomNav (3 tabs)

- **Phase 5 — Testing & Polish** (Stream D):
  - Fix TD-001: N+1 query leaderboard API → batch user names
  - Fix TD-002: CORS `*` → `MINI_APP_URL` restriction
  - QC: compile 10/10 Python + miniapp build OK

- **Phase 4 — Gamification Services** (Stream A, Wave 1):

  - `services/gamification_service.py` — Hệ thống điểm, streak, leaderboard, milestones (8 functions)
  - `services/mood_service.py` — Mood tracking, burnout detection, mood stats (4 functions)
  - `services/checkin_service.py` — Thêm `mood` param + `process_gamification_after_checkin()` orchestrator

- **Phase 4 — Gamification Bot** (Stream B, Wave 2):
  - `bot/handlers/gamification.py` — `/leaderboard`, `/points` commands, streak display
  - `bot/handlers/mood.py` — Mood prompt sau check-in, burnout alert (3 ngày SOS liên tiếp)
  - `bot/handlers/_helpers.py` — `handle_post_checkin()` integration helper
  - 6 handlers wired: GPS, WiFi, QR, NFC, WFH, checkout đều gọi gamification + mood

- **Phase 4 — Mini App** (Stream C, Wave 2):
  - `miniapp/` — React (Vite + TailwindCSS) Telegram Mini App
  - Dashboard: check-in history, stats, leaderboard, mood

- **Phase 4 — Mini App API** (Stream D, Wave 2):
  - `services/auth_service.py` — Telegram initData HMAC-SHA256 validation
  - `api/me.py` — User dashboard data endpoint
  - `api/checkins.py` — Paginated check-in history
  - `api/leaderboard.py` — Top 10 leaderboard + user rank

- **Phase 4 — Testing & Launch** (Stream E, Wave 3):
  - `api/cron/weekly.py` — Weekly leaderboard + streak reminder cron (Monday 9:00 AM)
  - `.github/workflows/cron-reminders.yml` — Thêm weekly schedule
  - `docs/QC_REPORT.md` — Compile check 18/18, miniapp build OK, 1 P0 bug fixed

- **Phase 3 — Services Foundation** (Stream A, Wave 1):
  - `services/config_service.py` — CRUD system_config (get/set upsert, get_all)
  - `services/leave_service.py` — Leave request CRUD + business logic (auto business days, trừ phép khi approve, remaining days)
  - `services/report_service.py` — Daily text report, weekly summary, monthly Excel export (2 sheets: Tổng hợp + Chi tiết)
  - `services/user_service.py` — Thêm get_all_users, update_user, deactivate_user, get_users_by_role
  - `requirements.txt` — Uncomment openpyxl==3.1.2

- **Phase 3 — Admin Panel** (Stream B, Wave 2):
  - `bot/handlers/admin_panel.py` — Admin Panel mới (tách riêng khỏi admin.py 730 lines)
  - `/admin` command → menu inline: quản lý nhân viên, cài đặt hệ thống, toggle check-in methods
  - Quản lý nhân viên: list phân trang, xem chi tiết, đổi role, vô hiệu hóa
  - Cài đặt hệ thống: sửa giờ làm, quỹ muộn, toggle GPS/WiFi/QR/NFC/Manual → lưu system_config
  - Lịch sử check-in: xem 30 ngày gần nhất từng nhân viên (giờ in/out, method, ontime/late)

- **Phase 3 — Leave Management** (Stream C, Wave 2):
  - `bot/handlers/leave.py` — Xin nghỉ phép (/leave, /xinnghỉ, /xinnghi)
  - ConversationHandler: chọn loại → ngày bắt đầu → ngày kết thúc → lý do → xác nhận → gửi admin group
  - Admin duyệt/từ chối inline buttons → notify user kết quả
  - Trừ ngày phép tự động khi approve loại 'annual'
  - `/phep` — Xem ngày phép còn lại + 5 đơn nghỉ gần nhất

- **Phase 3 — Report System** (Stream D, Wave 3):
  - `bot/handlers/report.py` — /report today|week|month, /baocao (alias)
  - `/report today` — text summary nhanh (có mặt, vắng, WFH, muộn, nghỉ phép)
  - `/report week` — bảng tổng hợp tuần (monospace text)
  - `/report month` — bảng tổng hợp tháng + gửi Excel file
  - `api/cron/daily_report.py` — Cron 9:15 AM gửi daily report vào admin group
  - `.github/workflows/cron-reminders.yml` — Thêm schedule 02:15 UTC (9:15 AM UTC+7)

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

- **Phase 6 — Stream A: Fix API & Auth** (Wave 1):
  - `api/me.py` — Fix field names match TS types (`total→total_days`, `late→late_days`, `wfh→wfh_days`). Thêm `leave_days`, `ontime_percentage`. Handle `get_user_stats()` exception
  - `api/checkins.py` — Thêm error handling chi tiết (log telegram_id + month), trả `{ok: false, error}` nhất quán
  - `api/leave.py` — Validate year range (2020-2100), thêm `ok` field trong error responses, log context chi tiết
  - `services/auth_service.py` — `validate_telegram_init_data()` trả `tuple[bool, str]` thay vì `bool`. Auth errors phân biệt: Missing header / Invalid signature / Token expired

- **Miniapp 404**: Fix deployment — Vercel không build miniapp do `.vercelignore` exclude `index.html`
  - Thêm `installCommand` + `buildCommand` vào `vercel.json`
  - Set `outputDirectory: "."` cho Python serverless + static miniapp
  - Xóa source `index.html` sau build để rewrites serve `dist/index.html`
  - Set `NODE_VERSION=22` trên Vercel (Vite 7 + Tailwind v4 yêu cầu)

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
