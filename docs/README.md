# 🔴 Pyng — BSMlabs Check-in Bot

> **"Ping your presence"** — Chấm công BSMlabs qua Telegram, không app, không phần cứng đắt tiền, không rườm rà.

---

## ✨ Tính năng chính

- **4 phương thức check-in** tự động dự phòng lẫn nhau: GPS · WiFi · QR · NFC
- **Gamification**: điểm thưởng, streak, leaderboard hàng tháng
- **Mood tracking**: đo nhiệt độ team sau mỗi check-in
- **Admin panel** ngay trong Telegram: set geofence, whitelist WiFi, duyệt thủ công
- **Báo cáo tự động**: Excel cuối ngày/tuần/tháng gửi thẳng vào group HR
- **Telegram Mini App**: dashboard đẹp, lịch sử cá nhân, xin phép nghỉ

---

## 🚀 Quick Start

### Yêu cầu

- Python 3.11+
- Supabase account (đã có)
- Vercel account (đã có)
- Telegram Bot Token (lấy từ [@BotFather](https://t.me/BotFather))
- GitHub repo (để CI/CD + GitHub Actions Cron)

### Cài đặt local

```bash
# Clone repo
git clone https://github.com/bsmlabs/pyng
cd pyng

# Tạo virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Cài dependencies
pip install -r requirements.txt

# Copy và điền config
cp .env.example .env
```

### Cấu hình `.env`

```env
# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here
WEBHOOK_URL=https://pyng.vercel.app

# Database
DATABASE_URL=postgresql://user:password@host:5432/checkin_db

# Check-in Settings
DEFAULT_GEOFENCE_RADIUS=100          # mét
QR_CODE_EXPIRE_SECONDS=30
OFFICE_WIFI_SSID=YourOfficeWiFi      # có thể set nhiều, cách nhau dấu phẩy

# Optional - Face Verification
FACEPP_API_KEY=
FACEPP_API_SECRET=

# Admin
ADMIN_TELEGRAM_IDS=123456789,987654321
```

### Chạy local

```bash
# Khởi tạo database
python scripts/init_db.py

# Chạy bot (polling mode cho dev)
python main.py --mode polling
```

### Deploy lên Vercel

```bash
npm install -g vercel
vercel login
vercel --prod
```

→ Xem chi tiết: [DEPLOYMENT.md](./DEPLOYMENT.md)

---

## 📱 Cách nhân viên dùng

```
1. Tìm bot: @PyngBot
2. Gõ /start → đăng ký bằng email công ty
3. Mỗi sáng: nhận thông báo → bấm CHECK IN
4. Chọn phương thức phù hợp (GPS / WiFi / QR / NFC)
5. Done ✅
```

→ Hướng dẫn đầy đủ: [USAGE.md](./USAGE.md)

---

## 🗂️ Cấu trúc thư mục

```
pyng/
├── api/
│   ├── webhook.py           # Nhận update từ Telegram
│   ├── cron/
│   │   ├── morning.py       # GitHub Actions gọi — nhắc check-in
│   │   ├── evening.py       # Nhắc check-out
│   │   ├── report.py        # Daily report
│   │   ├── qr_refresh.py    # Refresh QR token
│   │   └── auto_checkout.py # Tự động check-out 23:59
│   └── qr/
│       └── current.py       # QR display page fetch
├── bot/
│   ├── handlers/
│   │   ├── checkin.py       # Xử lý check-in/out
│   │   ├── admin.py         # Admin commands
│   │   ├── report.py        # Báo cáo
│   │   └── registration.py  # Đăng ký nhân viên
│   ├── validators/
│   │   ├── gps.py           # Kiểm tra geofence
│   │   ├── wifi.py          # Kiểm tra WiFi
│   │   ├── qr.py            # Sinh & kiểm tra QR
│   │   └── nfc.py           # Xử lý NFC token
│   └── keyboards.py         # Inline keyboards
├── config/
│   └── settings.py          # Cấu hình toàn cục
├── db/
│   ├── models.py            # SQLAlchemy models
│   ├── migrations/
│   └── queries.py           # DB helpers
├── services/
│   ├── gamification.py      # Điểm, streak, leaderboard
│   ├── report_generator.py  # Export Excel
│   └── face_verify.py       # Face++ integration (optional)
├── miniapp/                 # Telegram Mini App (React)
├── qr/
│   └── index.html           # QR display page (static)
├── vercel.json
├── requirements.txt
├── .env.example
└── .github/workflows/       # Cron scheduler (thay APScheduler)
```

---

## 📊 Tech Stack

| Layer         | Tech                        |
| ------------- | --------------------------- |
| Bot Framework | python-telegram-bot v21     |
| Database      | PostgreSQL via Supabase     |
| Hosting       | Vercel Serverless           |
| Scheduler     | GitHub Actions Cron         |
| Report        | openpyxl                    |
| QR Code       | qrcode + Pillow             |
| Mini App      | React + Vite + Tailwind     |
| Brand color   | `#FC3C44` (Apple Music Red) |

→ Chi tiết: [TECH_STACK.md](./TECH_STACK.md)

---

## 📄 Tài liệu

| File                                               | Mô tả                        |
| -------------------------------------------------- | ---------------------------- |
| [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md)         | Tóm tắt dự án cho AI/dev mới |
| [PRD.md](./PRD.md)                                 | Product Requirements         |
| [ARCHITECTURE.md](./ARCHITECTURE.md)               | System Design & DB Schema    |
| [BOT_FLOWS.md](./BOT_FLOWS.md)                     | Conversation Flows           |
| [DEV_ROADMAP.md](./DEV_ROADMAP.md)                 | Lộ trình phát triển          |
| [GAMIFICATION_DESIGN.md](./GAMIFICATION_DESIGN.md) | Hệ thống điểm & game hóa     |
| [DEPLOYMENT.md](./DEPLOYMENT.md)                   | Hướng dẫn deploy             |
| [USAGE.md](./USAGE.md)                             | Hướng dẫn người dùng         |
| [KNOWN_ISSUES.md](./KNOWN_ISSUES.md)               | Bugs & edge cases            |
| [PRIVACY_POLICY.md](./PRIVACY_POLICY.md)           | Chính sách dữ liệu           |
| [DECISIONS.md](./DECISIONS.md)                     | Lý do chọn công nghệ         |

---

## 📝 License

MIT — Tự do sử dụng nội bộ.
