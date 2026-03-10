# PROJECT_CONTEXT.md — Pyng / BSMlabs Check-in Bot

> ⚡ File này dùng để AI (hoặc dev mới) đọc nhanh toàn bộ dự án trong 2 phút.  
> Để hiểu sâu hơn từng phần, đọc file tương ứng được link bên dưới.

---

## 1. Dự án là gì?

**Pyng** — Telegram check-in bot cho BSMlabs. _"Ping your presence."_  
Hệ thống chấm công nội bộ hoàn toàn qua Telegram, không cần app riêng, không cần phần cứng đắt tiền.  
Chi phí vận hành: **$0/tháng**.

|                  |                             |
| ---------------- | --------------------------- |
| **Bot username** | `@PyngBot`                  |
| **Màu chủ đạo**  | `#FC3C44` (Apple Music Red) |
| **Tagline**      | _"Ping your presence"_      |

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

## 6. Tech Stack (tóm tắt)

- **Bot + Mini App**: Python 3.11 + `python-telegram-bot` v21 → **Vercel Serverless**
- **Database**: **Supabase** PostgreSQL (team đã quen)
- **Scheduler**: **GitHub Actions Cron** (thay APScheduler/Railway, $0)
- **QR Token**: Supabase (không cần Redis — đủ dùng cho <50 người)
- **Mini App**: React 18 + Vite → Vercel

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
    └── 23:59 → Auto check-out

         ↓ tất cả đọc/ghi
    Supabase PostgreSQL
```

→ Chi tiết: [ARCHITECTURE.md](./ARCHITECTURE.md)

## 7. Tính năng nổi bật

- ✅ 4 phương thức check-in dự phòng lẫn nhau
- ✅ Gamification: điểm, streak, leaderboard
- ✅ Mood tracking sau mỗi check-in
- ✅ Báo cáo tự động cuối ngày/tuần/tháng (Excel)
- ✅ Admin set geofence range ngay trong bot (không cần vào server)
- ✅ Telegram Mini App cho dashboard đẹp

## 8. Trạng thái dự án

- **Phase**: MVP Planning
- **Target go-live**: 4 tuần từ kick-off
- **Team size**: 1–2 devs

→ Lộ trình chi tiết: [DEV_ROADMAP.md](./DEV_ROADMAP.md)

## 9. Các file tài liệu

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
