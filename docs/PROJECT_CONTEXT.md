# PROJECT_CONTEXT.md — Pyng / BSMlabs Check-in Bot

> ⚡ File này dùng để AI (hoặc dev mới) đọc nhanh toàn bộ dự án trong 2 phút.  
> Để hiểu sâu hơn từng phần, đọc file tương ứng được link bên dưới.  
> Cập nhật lần cuối: 2026-03-12

---

## 1. Dự án là gì?

**Pyng** — Telegram check-in bot cho BSMlabs. _"Ping your presence."_  
Hệ thống chấm công nội bộ hoàn toàn qua Telegram, không cần app riêng, không cần phần cứng đắt tiền.  
Chi phí vận hành: **$0/tháng**.

|                  |                             |
| ---------------- | --------------------------- |
| **Mô hình**      | Internal tool               |
| **Bot username** | `@pyng85111_bot`            |
| **Màu chủ đạo**  | `#FC3C44` (Apple Music Red) |
| **Tagline**      | _"Ping your presence"_      |
| **Deploy**       | https://pyng.vercel.app     |

## 2. Thông tin BSMlabs

|                 |                                            |
| --------------- | ------------------------------------------ |
| **Văn phòng**   | 219 Trung Kính, Yên Hòa, Cầu Giấy, Hà Nội  |
| **Giờ làm**     | 08:45 – 17:45, Thứ 2 – Thứ 6               |
| **Quỹ đi muộn** | 180 phút/tháng (tự động trừ, reset ngày 1) |
| **WFH**         | Tối đa 2 lần/tháng                         |
| **Nhân viên**   | <50 người                                  |

## 3. Vấn đề cần giải quyết

- Chấm công truyền thống (thẻ từ, sổ ký tay) rườm rà, dễ gian lận
- App chấm công riêng → nhân viên không muốn cài thêm
- Công ty nhỏ không có ngân sách cho hệ thống HR lớn

## 4. Giải pháp

Bot Telegram với **4 phương thức check-in dự phòng**, nhân viên dùng cái nào tiện nhất:

| Phương thức     | Cách hoạt động                                     | Độ ưu tiên |
| --------------- | -------------------------------------------------- | ---------- |
| 📍 GPS Geofence | Gửi location, bot kiểm tra trong bán kính 120m     | Primary    |
| 📶 WiFi nội bộ  | Gửi tên WiFi đang kết nối, bot đối chiếu whitelist | Primary    |
| 📱 QR Code      | Scan QR động tại văn phòng (expire 5 phút)         | Backup     |
| 🏷️ NFC Tag      | Chạm thẻ/điện thoại vào tag NFC ở cửa              | Backup     |

Nếu tất cả fail → nhân viên gửi ảnh selfie kèm ghi chú, admin duyệt thủ công.

## 5. Người dùng

- **Nhân viên**: check-in/out, xem lịch sử, xin nghỉ, gửi các loại request
- **Admin/HR**: cấu hình geofence, WiFi whitelist, xem báo cáo, quản lý quỹ muộn
- **Manager**: xem dashboard team, duyệt request, nhận alert burnout

## 6. Tech Stack

| Layer     | Technology                 | Version / Notes                |
| --------- | -------------------------- | ------------------------------ |
| Language  | Python                     | 3.11+                          |
| Bot       | python-telegram-bot        | v21.5 (async, webhook)         |
| Database  | PostgreSQL (Supabase)      | Free tier 500MB                |
| Hosting   | Vercel Serverless          | Free — auto-deploy từ GitHub   |
| Scheduler | GitHub Actions Cron        | Free — thay APScheduler, $0    |
| QR Store  | Supabase (không cần Redis) | Đủ dùng cho <50 người          |
| Mini App  | React 18 + Vite + Tailwind | TypeScript, @twa-dev/sdk       |
| Report    | openpyxl                   | Xuất Excel (Phase 2+)          |
| QR Gen    | qrcode + Pillow            | QR image generation (Phase 2+) |
| Geo       | geopy                      | v2.4.1 — distance, geofence    |
| Validate  | pydantic                   | v2.5.3                         |
| HTTP      | httpx                      | v0.27.0                        |
| Config    | python-dotenv              | v1.0.0                         |
| Linting   | ruff                       | Configured in project          |

→ Chi tiết: [TECH_STACK.md](./TECH_STACK.md)

## 7. Kiến trúc tóm tắt

```
Telegram App
    │
    ▼
Telegram Bot API (webhook)
    │
    ▼
Vercel Serverless Function /api/webhook
    ├── Check-in Handler
    │     ├── GPS Validator (120m radius — 219 Trung Kính)
    │     ├── WiFi Validator (BSMlabs_WiFi / BSMlabs_5G)
    │     ├── QR Validator (5 phút expire)
    │     └── NFC Validator
    ├── Request Handler (WFH, nghỉ phép, OT, công tác...)
    ├── Late Budget Tracker (180 phút/tháng)
    ├── WFH Counter (2 lần/tháng)
    └── Report Generator

GitHub Actions (Cron)
    ├── 08:30 → Nhắc check-in
    ├── 17:45 → Nhắc check-out
    ├── 09:15 → Daily report → HR group
    ├── */5   → Refresh QR token (giờ làm việc)
    ├── Mon 09:00 → Weekly leaderboard + streak reminder
    └── 23:59 → Auto check-out

         ↓ tất cả đọc/ghi
    Supabase PostgreSQL
```

- **Cấu trúc repo**: Monorepo — `bot/`, `api/`, `services/`, `db/`, `config/`, `miniapp/`, `qr/`
- **API format**: REST — webhook `https://pyng.vercel.app/api/webhook`
- **Data flow**: `Telegram App ←→ Vercel Serverless ←→ Supabase PostgreSQL`

→ Chi tiết: [ARCHITECTURE.md](./ARCHITECTURE.md)

## 8. Modules hiện có

### Bot Engine (`bot/`)

- `bot/app.py` — Application factory, đăng ký handlers
- `bot/handlers/_helpers.py` — Shared utils (get_active_user, ontime status, time format)
- `bot/handlers/start.py` — Registration flow + deep link routing (QR/NFC)
- `bot/handlers/admin.py` — Admin approval, GPS, WiFi, QR config, NFC management, manual approval
- `bot/handlers/admin_panel.py` — Admin Panel: menu /admin, quản lý NV, cài đặt, lịch sử (Phase 3)
- `bot/handlers/checkin.py` — Re-export module (GPS, WiFi, QR, Manual, Checkout, WFH)
- `bot/handlers/gps_checkin.py` — GPS check-in (/checkin + location)
- `bot/handlers/wifi_checkin.py` — WiFi check-in (/checkin_wifi)
- `bot/handlers/qr_checkin.py` — QR check-in (/checkin_qr + deep link)
- `bot/handlers/nfc_checkin.py` — NFC check-in (deep link /start nfc_TOKEN)
- `bot/handlers/manual_checkin.py` — Manual fallback (/manual + selfie + admin approval)
- `bot/handlers/checkout.py` — Check-out (/checkout)
- `bot/handlers/wfh.py` — WFH flow (/wfh)
- `bot/handlers/leave.py` — Leave management: xin nghỉ, duyệt, xem phép (Phase 3)
- `bot/handlers/report.py` — Report commands: /report today|week|month (Phase 3)
- `bot/handlers/gamification.py` — Leaderboard (/leaderboard, /xh), Points (/points, /diem) (Phase 4)
- `bot/handlers/mood.py` — Mood prompt sau check-in, burnout alert cho admin (Phase 4)
- `bot/validators/gps_validator.py` — Geofence check (geopy), spoofing detection
- `bot/validators/wifi_validator.py` — SSID whitelist validation

### API (`api/`)

- `api/webhook.py` — Vercel serverless endpoint, nhận Telegram webhook
- `api/qr/current.py` — GET /api/qr/current (JSON + base64 QR image)
- `api/cron/morning.py` — Nhắc check-in 8:30 cho active users chưa check-in
- `api/cron/evening.py` — Nhắc check-out 17:45 cho users đã check-in chưa checkout
- `api/cron/qr_refresh.py` — Cron tạo QR mới mỗi 5 phút (giờ làm việc)
- `api/cron/daily_report.py` — Báo cáo hàng ngày 9:15 AM gửi admin group (Phase 3)
- `api/cron/weekly.py` — Weekly leaderboard + streak reminder (Monday 9:00 AM) (Phase 4)
- `api/me.py` — GET /api/me — User dashboard data (info + gamification + stats) (Phase 4)
- `api/checkins.py` — GET /api/checkins — Paginated check-in history (Phase 4)
- `api/leaderboard.py` — GET /api/leaderboard — Top 10 + user rank (Phase 4)

### Services (`services/`)

- `services/user_service.py` — Register, activate, reject, is_admin, CRUD admin (Phase 3)
- `services/checkin_service.py` — Checkin/checkout/WFH, working hours, duplicate check
- `services/office_service.py` — Office CRUD, WiFi whitelist management
- `services/qr_service.py` — QR session CRUD, generate QR image, validate token
- `services/nfc_service.py` — NFC token CRUD, validate, list, deactivate
- `services/cron_helpers.py` — Shared cron utilities (auth, Telegram API via httpx)
- `services/config_service.py` — System config CRUD (Phase 3)
- `services/leave_service.py` — Leave request CRUD + business logic (Phase 3)
- `services/report_service.py` — Daily/weekly/monthly reports + Excel export (Phase 3)
- `services/gamification_service.py` — Points, streak, leaderboard, user stats (Phase 4)
- `services/mood_service.py` — Mood tracking, burnout detection, mood stats (Phase 4)
- `services/auth_service.py` — Telegram initData HMAC-SHA256 validation, API auth (Phase 4)
- `services/salary_service.py` — Salary calculation: basic + OT - late deductions - unpaid leave (Phase 6)

### Database (`db/`)

- `db/client.py` — REST wrapper qua httpx (PostgREST API, service_role_key)
- `db/schema.sql` — 10 tables + indexes + RLS

### Config (`config/`)

- `config/settings.py` — Centralized settings từ env vars (pydantic)
- `config/timezone.py` — Shared timezone helper (singleton ZoneInfo)

### QR Display (`qr/`)

- `qr/index.html` — Static page, client-side polling QR từ Supabase

### Mini App (`miniapp/`)

- React 18 + Vite + Tailwind — Dashboard cá nhân (Phase 4)

## 9. API Endpoints

### Bot Webhook

| Method | Path           | Mô tả                         |
| ------ | -------------- | ----------------------------- |
| POST   | `/api/webhook` | Nhận Telegram webhook updates |

### Cron (GitHub Actions gọi)

| Method | Path                   | Mô tả                                           |
| ------ | ---------------------- | ----------------------------------------------- |
| POST   | `/api/cron/morning`    | Nhắc check-in 08:30 (cần `CRON_SECRET`)         |
| POST   | `/api/cron/evening`    | Nhắc check-out 17:45 (cần `CRON_SECRET`)        |
| POST   | `/api/cron/daily_report` | Báo cáo hàng ngày 09:15 (Phase 3)             |
| POST   | `/api/cron/qr_refresh` | Refresh QR mỗi 5 phút (Phase 2)                |
| POST   | `/api/cron/weekly`     | Leaderboard + streak reminder Monday 09:00 (Phase 4) |

### Mini App API (Phase 4) — Auth: `X-Telegram-Init-Data` header

| Method | Path               | Mô tả                              |
| ------ | ------------------ | ---------------------------------- |
| GET    | `/api/me`          | User info + gamification + stats   |
| GET    | `/api/checkins`    | Paginated check-in history         |
| GET    | `/api/leaderboard` | Top 10 + user rank (month/alltime) |
| GET    | `/api/salary`      | Monthly salary summary (Phase 6)   |

## 10. Tính năng nổi bật

- ✅ 4 phương thức check-in dự phòng lẫn nhau
- ✅ Gamification: điểm, streak, leaderboard
- ✅ Mood tracking sau mỗi check-in
- ✅ Báo cáo tự động cuối ngày/tuần/tháng (Excel)
- ✅ Admin set geofence range ngay trong bot (không cần vào server)
- ✅ Telegram Mini App cho dashboard đẹp

## 11. Trạng thái dự án

- **Version**: 0.5.0 (Unreleased)
- **Phase**: Phase 5 — Enhancement (hoàn thành)
- **Target go-live**: 4 tuần từ kick-off
- **Team size**: 1–2 devs

### Unreleased changes

- Phase 0: Bot scaffold, webhook, /start, Supabase schema + seed
- Phase 1 Wave 1: DB client, services (user, checkin, office), validators (GPS, WiFi)
- Phase 1 Wave 2: Bot handlers (start, admin, checkin), cron reminders (morning, evening)
- Phase 2: QR System, NFC System, Manual Fallback — 4 phương thức check-in hoạt động
- Phase 3: Admin Panel (/admin), Leave Management (/leave, /phep), Reports (/report, cron daily)
- Phase 4: Gamification (points, streak, leaderboard), Mood tracking, Mini App dashboard, API endpoints, Weekly cron

### Next milestone

- Phase 6: Stabilize & Salary (Fix API 500, polish miniapp UX, tích hợp tính lương)

→ Lộ trình chi tiết: [DEV_ROADMAP.md](./DEV_ROADMAP.md)

## 12. Key Conventions

- **Commit format**: Conventional Commits (tiếng Việt): `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`
- **Naming**: `snake_case` cho Python files/variables, `kebab-case` cho config files
- **Modules**: Python packages với `__init__.py`
- **Config**: `.env` → `config/settings.py` (pydantic) → inject vào services
- **Architecture**: Tách biệt handler ↔ service ↔ validator ↔ DB client
- **Docs**: Luôn update docs trước/sau khi implement feature

## 13. Các file tài liệu

| File                                               | Nội dung                      |
| -------------------------------------------------- | ----------------------------- |
| [README.md](./README.md)                           | Setup & quick start           |
| [PRD.md](./PRD.md)                                 | Product requirements chi tiết |
| [ARCHITECTURE.md](./ARCHITECTURE.md)               | System design, DB schema, API |
| [BOT_FLOWS.md](./BOT_FLOWS.md)                     | Toàn bộ conversation flows    |
| [TECH_STACK.md](./TECH_STACK.md)                   | Dependencies, cấu hình        |
| [DEPLOYMENT.md](./DEPLOYMENT.md)                   | Hướng dẫn deploy + seed data  |
| [DEV_ROADMAP.md](./DEV_ROADMAP.md)                 | Timeline, phases              |
| [GAMIFICATION_DESIGN.md](./GAMIFICATION_DESIGN.md) | Hệ thống điểm, streak         |
| [DECISIONS.md](./DECISIONS.md)                     | Lý do chọn tech               |
| [PRIVACY_POLICY.md](./PRIVACY_POLICY.md)           | Chính sách dữ liệu            |
| [USAGE.md](./USAGE.md)                             | Hướng dẫn dùng cho nhân viên  |
| [KNOWN_ISSUES.md](./KNOWN_ISSUES.md)               | Bugs & edge cases đã biết     |
| [CHANGELOG.md](./CHANGELOG.md)                     | Lịch sử thay đổi              |
| [TASK_BOARD.md](./TASK_BOARD.md)                   | Tiến độ phase hiện tại        |

## 14. Context Size Guide

- Chỉ đọc file này: ~160 lines
- \+ TECH_STACK.md: ~+420 lines
- \+ ARCHITECTURE.md: ~+340 lines
- Ngưỡng cảnh báo: > 300 lines tổng → cân nhắc trim context

## 15. Reading Order / Onboarding

> Dành cho dev mới hoặc AI agent mới vào project. Đọc theo thứ tự ưu tiên.

**Tier 1 — Bắt buộc** (hiểu project):

1. `PROJECT_CONTEXT.md` ← file này
2. `DEV_ROADMAP.md` — biết đang ở phase nào
3. `ARCHITECTURE.md` — hiểu cấu trúc code + DB schema

**Tier 2 — Khi bắt đầu code**: 4. `BOT_FLOWS.md` — toàn bộ conversation flows 5. `KNOWN_ISSUES.md` — bugs đã biết + checklist go-live 6. `DECISIONS.md` — tại sao chọn tech/approach hiện tại

**Tier 3 — Khi deploy/ops**: 7. `DEPLOYMENT.md` — setup, monitoring, incident response, backup 8. `TECH_STACK.md` — dependencies, versions, config

**Tier 4 — Quy trình** (`.agents/`): 9. `workflows/` — `/parallel-phase`, `/new-feature`, `/task-completion`, `/qc`, `/code-review` 10. `templates/rules/` — coding conventions, security, error handling
