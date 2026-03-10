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

## Phase 0 — Setup (Ngày 1–2)

**Mục tiêu**: Môi trường dev sẵn sàng, bot cơ bản chạy được

**Tasks**:

- [ ] Tạo repo GitHub, setup branch strategy (`main`, `dev`, `feature/*`)
- [ ] Setup Python project, cài dependencies
- [ ] Tạo bot trên BotFather
- [ ] Kết nối Supabase, khởi tạo schema
- [ ] Deploy bot rỗng lên Vercel Serverless (webhook hoạt động)
- [ ] CI/CD: GitHub → Vercel auto deploy khi push main
- [ ] Setup GitHub Actions Cron workflows (nhắc, báo cáo, QR refresh)

**Done when**: Bot phản hồi `/start` trả về "Hello World" từ Vercel

---

## Phase 1 — MVP Core (Tuần 1)

**Mục tiêu**: Nhân viên có thể đăng ký và check-in bằng GPS + WiFi

### Tuần 1 - Ngày 3–5: User Registration & GPS

- [ ] Đăng ký nhân viên (`/start` flow)
- [ ] Admin approval flow
- [ ] GPS check-in với geofence validation
- [ ] Geopy distance calculation
- [ ] GPS spoofing detection (speed check)
- [ ] Lưu checkin vào DB
- [ ] Response sau check-in (thành công / thất bại)
- [ ] Admin set geofence qua bot (`/admin → GPS Settings`)

### Tuần 1 - Ngày 6–7: WiFi & Reminder

- [ ] WiFi check-in flow
- [ ] Admin quản lý WiFi whitelist
- [ ] Scheduler: nhắc check-in buổi sáng
- [ ] Scheduler: nhắc check-out buổi chiều
- [ ] Check-out flow
- [ ] WFH flow

**Done when**: 5 người test được check-in GPS + WiFi mỗi ngày

---

## Phase 2 — Check-in Methods (Tuần 2)

**Mục tiêu**: Thêm QR + NFC + Fallback thủ công

### Ngày 8–10: QR System

- [ ] QR code generator (qrcode + Pillow)
- [ ] QR token store trong Supabase (expire 5 phút)
- [ ] QR display web page (auto-refresh)
- [ ] Deep link handler: `/start qr_TOKEN`
- [ ] Validate QR: tồn tại, chưa used, chưa expired
- [ ] Admin: config expire time, xem QR display link

### Ngày 11–12: NFC System

- [ ] NFC token generator và lưu DB
- [ ] Deep link handler: `/start nfc_TOKEN`
- [ ] Admin: tạo NFC token, quản lý danh sách
- [ ] Hướng dẫn ghi NFC tag (gửi PDF trong bot)

### Ngày 13–14: Manual Fallback

- [ ] Flow "Gặp sự cố"
- [ ] Nhận ảnh selfie, lưu với metadata
- [ ] Admin notification + duyệt/từ chối
- [ ] Bulk approve

**Done when**: Cả 4 phương thức hoạt động, fallback hoạt động

---

## Phase 3 — Admin & Report (Tuần 3)

**Mục tiêu**: Admin có đủ công cụ quản lý, báo cáo tự động hoạt động

### Ngày 15–17: Admin Panel

- [ ] Admin panel đầy đủ (inline keyboard navigation)
- [ ] Quản lý nhân viên (thêm, xóa, sửa role)
- [ ] Xem lịch sử cá nhân từng người
- [ ] Cài đặt hệ thống (giờ làm, giờ nhắc, timezone)
- [ ] Toggle bật/tắt từng phương thức check-in

### Ngày 18–19: Leave Management

- [ ] Xin nghỉ phép flow
- [ ] Manager duyệt
- [ ] Trừ ngày phép tự động
- [ ] Xem số ngày phép còn lại

### Ngày 20–21: Báo cáo

- [ ] Daily report tự động (gửi group HR 9:30 AM)
- [ ] `/report today` — text nhanh
- [ ] Weekly report (Excel)
- [ ] Monthly report (Excel đầy đủ)
- [ ] Export theo khoảng thời gian tùy chọn

**Done when**: Admin tự vận hành được, báo cáo tự động chạy đúng giờ

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
