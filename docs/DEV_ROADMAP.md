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

## Phase 4 — Gamification & Polish (Tuần 4)

**Mục tiêu**: Trải nghiệm hoàn chỉnh, sẵn sàng go-live

### Ngày 22–24: Gamification

- [ ] Hệ thống điểm (xem GAMIFICATION_DESIGN.md)
- [ ] Streak tracking
- [ ] Leaderboard hàng tháng
- [ ] Mood tracking sau check-in
- [ ] Mood dashboard cho manager

### Ngày 25–26: Mini App

- [ ] React project setup (Vite + Tailwind)
- [ ] Telegram WebApp SDK integration
- [ ] Dashboard: lịch sử check-in cá nhân
- [ ] Biểu đồ giờ làm việc tháng
- [ ] Xin nghỉ qua Mini App
- [ ] Deploy lên Vercel

### Ngày 27–28: Testing & Launch

- [ ] Test toàn bộ flows với team 5–10 người
- [ ] Fix bugs từ feedback
- [ ] Kiểm tra edge cases (xem KNOWN_ISSUES.md)
- [ ] Viết USAGE.md gửi nhân viên
- [ ] Go-live với toàn bộ công ty

---

## Phase 5 — Enhancement (Tháng 2+)

Sau khi ổn định, có thể bổ sung:

| Feature                       | Ưu tiên | Effort |
| ----------------------------- | ------- | ------ |
| Face verification (Face++)    | Medium  | 3 ngày |
| Google Calendar sync          | Low     | 2 ngày |
| Slack/Notion integration      | Low     | 2 ngày |
| Overtime tracking             | Medium  | 2 ngày |
| Multi-office support nâng cao | Low     | 3 ngày |
| Analytics dashboard nâng cao  | Low     | 3 ngày |
| Tích hợp phần mềm lương       | High    | 1 tuần |

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
