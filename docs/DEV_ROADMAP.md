# DEV_ROADMAP.md — Lộ trình phát triển

---

## Tổng quan

```
Week 1          Week 2          Week 3          Week 4
  │               │               │               │
  ▼               ▼               ▼               ▼
[Foundation]  [Check-in Core] [Admin & Report] [Polish & Launch]
```

---

## Phase 0 — Setup ✅ (Hoàn thành 2026-03-10)

**Mục tiêu**: Môi trường dev sẵn sàng, bot cơ bản chạy được

**Tasks**:

- [x] Tạo repo GitHub (`nsongha/Pyng`)
- [x] Setup Python project, cài dependencies
- [x] Tạo bot trên BotFather (`@pyng85111_bot`)
- [x] Kết nối Supabase, khởi tạo schema (10 tables + seed data)
- [x] Deploy bot lên Vercel Serverless (https://pyng.vercel.app)
- [x] CI/CD: GitHub → Vercel auto deploy khi push main

**Done when**: ~~Bot phản hồi `/start` trả về "Hello World" từ Vercel~~ ✅ Done

---

## Phase 1 — MVP Core (Tuần 1)

**Mục tiêu**: Nhân viên có thể đăng ký và check-in bằng GPS + WiFi

### Tuần 1 - Ngày 3–5: User Registration & GPS

- [x] Đăng ký nhân viên (`/start` flow)
- [x] Admin approval flow
- [x] GPS check-in với geofence validation
- [x] Geopy distance calculation
- [x] GPS spoofing detection (speed check)
- [x] Lưu checkin vào DB
- [x] Response sau check-in (thành công / thất bại)
- [x] Admin set geofence qua bot (`/admin → GPS Settings`)

### Tuần 1 - Ngày 6–7: WiFi & Reminder

- [x] WiFi check-in flow
- [x] Admin quản lý WiFi whitelist
- [x] Scheduler: nhắc check-in buổi sáng
- [x] Scheduler: nhắc check-out buổi chiều
- [x] Check-out flow
- [x] WFH flow
- [x] Setup GitHub Actions Cron workflows (nhắc, báo cáo, QR refresh) ← dời từ Phase 0

**Done when**: 5 người test được check-in GPS + WiFi mỗi ngày

---

## Phase 2 — Check-in Methods (Tuần 2) ✅ (Hoàn thành 2026-03-11)

**Mục tiêu**: Thêm QR + NFC + Fallback thủ công

### Ngày 8–10: QR System

- [x] QR code generator (qrcode + Pillow)
- [x] QR token store trong Supabase (expire 5 phút)
- [x] QR display web page (auto-refresh + countdown)
- [x] Deep link handler: `/start qr_TOKEN`
- [x] Validate QR: tồn tại, chưa used, chưa expired
- [x] Admin: config expire time, xem QR display link (/admin_qr)
- [x] Manual QR input: `/checkin_qr` (gõ mã 8 ký tự)
- [x] API endpoint: `/api/qr/current` (JSON + base64 image)
- [x] Cron endpoint: `/api/cron/qr_refresh` (mỗi 5 phút)

### Ngày 11–12: NFC System

- [x] NFC token generator và lưu DB
- [x] Deep link handler: `/start nfc_TOKEN`
- [x] Admin: tạo NFC token, quản lý danh sách (/admin_nfc)
- [x] Hiển thị deep link URL cho mỗi token (để ghi vào NFC tag)

### Ngày 13–14: Manual Fallback

- [x] Flow "Gặp sự cố" (/manual, /checkin_manual)
- [x] Nhận ảnh selfie, lưu với metadata (photo + lý do)
- [x] Admin notification + duyệt/từ chối (inline buttons trên admin group)
- [ ] Bulk approve (dời sang Phase 3)

**Done when**: ~~Cả 4 phương thức hoạt động, fallback hoạt động~~ ✅ Done

---

## Phase 3 — Admin & Report (Tuần 3) ✅ (Hoàn thành 2026-03-11)

**Mục tiêu**: Admin có đủ công cụ quản lý, báo cáo tự động hoạt động

### Wave 1: Services Foundation ✅

- [x] Config Service — system_config CRUD (get/set/get_all)
- [x] Leave Service — leave request CRUD + business logic
- [x] Report Service — daily/weekly/monthly reports + Excel export
- [x] User Service mở rộng — admin CRUD (get_all, update, deactivate, filter by role)
- [x] Uncomment openpyxl dependency

### Wave 2: Admin Panel + Leave ✅

- [x] Admin panel đầy đủ (inline keyboard navigation /admin)
- [x] Quản lý nhân viên (list, sửa role, deactivate)
- [x] Xem lịch sử check-in cá nhân (30 ngày)
- [x] Cài đặt hệ thống (giờ làm, quỹ muộn)
- [x] Toggle bật/tắt từng phương thức check-in
- [x] Xin nghỉ phép flow (/leave, /xinnghỉ)
- [x] Admin duyệt/từ chối nghỉ phép
- [x] Trừ ngày phép tự động (annual leave)
- [x] Xem số ngày phép còn lại (/phep)

### Wave 3: Report ✅

- [x] Daily report tự động (gửi admin group 9:15 AM)
- [x] `/report today` — text nhanh
- [x] `/report week` — tổng hợp tuần (text)
- [x] `/report month` — tổng hợp tháng (text + Excel)
- [ ] Export theo khoảng thời gian tùy chọn (dời sang Phase 5)

**Done when**: ~~Admin tự vận hành được, báo cáo tự động chạy đúng giờ~~ ✅ Done

---

## Phase 4 — Gamification & Polish (Tuần 4) ✅ (Hoàn thành 2026-03-11)

**Mục tiêu**: Trải nghiệm hoàn chỉnh, sẵn sàng go-live

### Ngày 22–24: Gamification

- [x] Hệ thống điểm (xem GAMIFICATION_DESIGN.md)
- [x] Streak tracking
- [x] Leaderboard hàng tháng
- [x] Mood tracking sau check-in
- [x] Mood dashboard cho manager

### Ngày 25–26: Mini App

- [x] React project setup (Vite + Tailwind)
- [x] Telegram WebApp SDK integration
- [x] Dashboard: lịch sử check-in cá nhân
- [x] Biểu đồ giờ làm việc tháng
- [x] Xin nghỉ qua Mini App (**moved to Phase 5** → ✅)
- [x] Deploy lên Vercel

### Ngày 27–28: Testing & Launch

- [x] Test toàn bộ flows (QC Report: compile 18/18 + miniapp build)
- [x] Fix bugs từ testing (P0: wire gamification vào 6 handlers)
- [x] Kiểm tra edge cases (xem KNOWN_ISSUES.md)
- [x] Weekly cron: leaderboard + streak reminder
- [ ] Go-live với toàn bộ công ty (chờ deploy)

**Done when**: ~~Gamification chạy, Mini App hoạt động, test OK~~ ✅ Done

---

## Phase 5 — Enhancement ✅ (Hoàn thành 2026-03-12)

**Mục tiêu**: Nâng cấp trải nghiệm — chart, leave form Mini App, overtime tracking, export mở rộng, fix tech debt

**Tasks completed (21/21)**:

- [x] Overtime Service: tracking + tính OT (30 phút grace, cap 4h/ngày)
- [x] Report export theo khoảng ngày tùy chọn (max 90 ngày)
- [x] Bot command: `/report YYYY-MM-DD YYYY-MM-DD` (custom date range Excel)
- [x] Bulk approve manual check-in (inline button)
- [x] API: GET `/api/checkins/chart` (chart data with trend)
- [x] API: POST `/api/leave/request` (leave form + admin notification)
- [x] API: GET `/api/leave/my` (leave list + balance)
- [x] API: GET `/api/overtime` (monthly OT data)
- [x] Mini App: React Router + Bottom Navigation (3 tabs)
- [x] Mini App: Chart components (WorkingHoursChart + AttendanceDonut + recharts)
- [x] Mini App: Charts page (month selector + stats + trend)
- [x] Mini App: OvertimeCard + sparkline
- [x] Mini App: Leave form (date picker + validation + haptic feedback)
- [x] Mini App: Leave list (status badges + pull-to-refresh)
- [x] Mini App: Leave page (tab toggle: list / form + balance card)
- [x] Fix TD-001: N+1 query leaderboard (batch user names)
- [x] Fix TD-002: CORS restriction (MINI_APP_URL fallback)
- [x] QC test: compile + miniapp build + regression
- [x] Code review: 0 P0, 1 P1 fixed (bulk approve register)

**Done when**: ~~Charts + Leave form + Overtime + Export mở rộng hoạt động~~ ✅ Done

---

## Phase 6 — Stabilize & Salary ✅ (Hoàn thành 2026-03-13)

**Mục tiêu**: Fix API lỗi trên mini app, polish UX 3 trang hiện có, tích hợp tính lương

### Wave 1: Fix API & Auth (P0) — ✅ (Hoàn thành 2026-03-12)

- [x] Fix CORS headers bị ghi vào response body → `fetch().json()` crash (API-001)
- [x] Fix column `is_ontime` không tồn tại trong DB → PostgREST error (API-002)
- [x] Fix Token expired — `MAX_AUTH_AGE_SECONDS` 3600→86400 (API-003)
- [x] Chuyển CORS headers sang `vercel.json` edge config
- [x] Bỏ CSP `default-src 'self'` trên API routes
- [x] Verify 3 trang Mini App (Dashboard, Thống kê, Nghỉ phép) hoạt động trên production

### Wave 2: Mini App Polish (P1) — ✅ (Hoàn thành 2026-03-12)

- [x] Error handling: hiển thị lỗi cụ thể thay vì generic "HTTP 500"
- [x] Empty states: UI đẹp hơn khi chưa có data (first-time user)
- [x] Loading states / skeleton consistent cả 3 trang
- [x] Offline fallback / retry logic cải thiện
- [x] Dark/light mode test trên Telegram

### Wave 3: Tích hợp phần mềm lương (High) — ✅ (Hoàn thành 2026-03-13)

- [x] Thiết kế salary calculation logic (basic salary + OT + deductions)
- [x] API endpoint: GET `/api/salary` (monthly salary summary)
- [x] Mini App: trang Lương (4 tab Bottom Nav)
- [x] Tích hợp dữ liệu check-in + OT + nghỉ phép vào tính lương
- [x] Export bảng lương (Excel) — GET `/api/salary/export` (admin only)

### Backlog (dời sang Phase 7+)

| Feature                       | Ưu tiên | Effort |
| ----------------------------- | ------- | ------ |
| Face verification (Face++)    | Medium  | 3 ngày |
| Google Calendar sync          | Low     | 2 ngày |
| Slack/Notion integration      | Low     | 2 ngày |
| Multi-office support nâng cao | Low     | 3 ngày |
| Analytics dashboard nâng cao  | Low     | 3 ngày |

**Done when**: ~~3 trang miniapp hoạt động đúng trên Telegram, tính lương cơ bản chạy được~~ ✅ Done

---

## Dependency & Risk

| Risk                            | Xác suất   | Ảnh hưởng  | Mitigations                         |
| ------------------------------- | ---------- | ---------- | ----------------------------------- |
| Telegram API rate limit         | Thấp       | Trung bình | Queue messages, exponential backoff |
| GPS không chính xác trong nhà   | Cao        | Cao        | WiFi là primary method song song    |
| NFC không hoạt động trên iOS cũ | Trung bình | Thấp       | QR là backup đủ tốt                 |
| Supabase free tier đầy          | Thấp       | Cao        | Monitor usage, cleanup định kỳ      |
| Vercel function timeout         | Thấp       | Trung bình | Paginate reports, async processing  |

---

## Definition of Done (DoD)

Một feature được coi là **Done** khi:

1. ✅ Code đã được review (nếu có team)
2. ✅ Happy path hoạt động
3. ✅ Edge cases chính đã xử lý
4. ✅ Error messages thân thiện với user
5. ✅ Đã test trên Telegram mobile (iOS hoặc Android)
6. ✅ Log đủ để debug nếu có lỗi
