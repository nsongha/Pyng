# TECH_STACK.md — Công nghệ & Cài đặt

---

## 1. Stack tổng quan

```
┌─────────────────────────────────────────────┐
│  LANGUAGE: Python 3.11+                      │
│  BOT FRAMEWORK: python-telegram-bot v21      │
│  DATABASE: PostgreSQL (Supabase)             │
│  HOSTING (Bot): Vercel Serverless Functions  │
│  SCHEDULER: GitHub Actions (Cron)            │
│  QR TOKEN STORE: Supabase (không cần Redis)  │
│  MINI APP: React 18 + Vite + Tailwind        │
│  MINI APP HOST: Vercel                       │
│  REPORT: openpyxl                            │
│  QR: qrcode + Pillow                         │
│  OPTIONAL: Face++ API                        │
└─────────────────────────────────────────────┘
```

### Tại sao không cần Redis?

QR token chỉ cần lưu 30–120 giây và query đơn giản → Supabase với index
trên `expire_at` là đủ. Không cần thêm một service nữa cho <50 người.

### Tại sao Vercel thay Railway?

Bot Telegram dùng Webhook — mỗi tin nhắn là một HTTP POST request độc lập,
không cần long-running process. Vercel Serverless Function xử lý tốt.
Scheduler (nhắc giờ, báo cáo) chạy qua GitHub Actions Cron — miễn phí hoàn toàn.
→ Xem chi tiết: [DECISIONS.md](./DECISIONS.md#adr-010)

---

## 2. Dependencies chi tiết

### `requirements.txt`

```txt
# Bot core
python-telegram-bot==21.5
python-telegram-bot[webhooks]

# Database
sqlalchemy==2.0.25
asyncpg==0.29.0
alembic==1.13.1
supabase==2.3.0

# QR Code
qrcode[pil]==7.4.2
Pillow==10.2.0

# Report
openpyxl==3.1.2

# Utilities
python-dotenv==1.0.0
httpx==0.26.0
pydantic==2.5.3

# Geo calculations
geopy==2.4.1

# API (Mini App backend + Cron endpoints)
fastapi==0.109.0
uvicorn==0.27.0
python-jose[cryptography]==3.3.0  # JWT

# Optional: Face verification
requests==2.31.0
```

> ✅ Không còn `redis` và `apscheduler` — scheduler chuyển sang GitHub Actions,
> QR token lưu thẳng vào Supabase.

---

## 3. Cấu hình môi trường

### `.env.example`

```env
# ==========================================
# TELEGRAM
# ==========================================
TELEGRAM_BOT_TOKEN=your_token_from_botfather
BOT_USERNAME=PyngBot
WEBHOOK_URL=https://your-project.vercel.app
WEBHOOK_PATH=/api/webhook

# ==========================================
# DATABASE (Supabase)
# ==========================================
DATABASE_URL=postgresql+asyncpg://postgres:password@db.xxxx.supabase.co:5432/postgres
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key  # Dùng cho cron jobs

# ==========================================
# BSMlabs OFFICE CONFIG
# ==========================================
OFFICE_NAME=BSMlabs Office
OFFICE_ADDRESS=219 Trung Kính, Yên Hòa, Cầu Giấy, Hà Nội
OFFICE_LAT=21.0285                # Tọa độ 219 Trung Kính (cần verify thực tế)
OFFICE_LNG=105.7968
DEFAULT_GEOFENCE_RADIUS_M=120     # Hơi rộng vì tòa nhà trong ngõ

# ==========================================
# WORK SCHEDULE — BSMlabs
# ==========================================
TIMEZONE=Asia/Ho_Chi_Minh
WORK_START=08:45
WORK_END=17:45
CHECKIN_REMIND=08:30              # Nhắc trước 15 phút
CHECKOUT_REMIND=17:45
DAILY_REPORT_TIME=09:15           # Báo cáo sau khi đã check-in xong
AUTO_CHECKOUT=23:59

# ==========================================
# BSMlabs POLICY CONFIG
# ==========================================
LATE_BUDGET_MINUTES=180           # Quỹ đi muộn: 3 tiếng = 180 phút/tháng
LATE_GRACE_MINUTES=5              # Dưới 5 phút không tính muộn
WFH_LIMIT_PER_MONTH=2            # Tối đa 2 lần WFH/tháng
QR_EXPIRE_SECONDS=300             # 5 phút (GitHub Actions Cron tối thiểu 5 phút)
MAX_GPS_ACCURACY_M=50
MAX_TRAVEL_SPEED_KMH=500          # Phát hiện GPS fake
MANUAL_CHECKIN_PHOTO_RETENTION_DAYS=30

# ==========================================
# OFFICE WIFI (seed, có thể config thêm qua bot)
# ==========================================
OFFICE_WIFI_SSIDS=BSMlabs_WiFi,BSMlabs_5G

# ==========================================
# ADMIN & GROUPS
# ==========================================
ADMIN_TELEGRAM_IDS=123456789      # Phân tách bằng dấu phẩy nếu nhiều admin
ADMIN_GROUP_ID=-1001234567890     # Group HR nhận báo cáo hàng ngày

# ==========================================
# CRON SECRET (bảo vệ endpoint cron)
# ==========================================
CRON_SECRET=your_random_secret_here  # GitHub Actions gửi header này để auth

# ==========================================
# JWT (Mini App)
# ==========================================
JWT_SECRET=your_random_secret_key_here
JWT_EXPIRE_HOURS=24

# ==========================================
# MINI APP
# ==========================================
MINI_APP_URL=https://pyng.vercel.app
QR_DISPLAY_URL=https://pyng.vercel.app/qr

# ==========================================
# OPTIONAL: Face++ API
# ==========================================
FACEPP_API_KEY=
FACEPP_API_SECRET=
```

---

## 4. Lý do chọn từng công nghệ

| Công nghệ                  | Lý do chọn                                                  | Thay thế được bằng |
| -------------------------- | ----------------------------------------------------------- | ------------------ |
| `python-telegram-bot` v21  | Async, mature, nhiều docs                                   | aiogram            |
| Supabase                   | Team đã quen, free tier 500MB, REST API sẵn có              | Neon.tech          |
| Vercel                     | Team đã quen, free, auto-deploy từ GitHub, CDN global       | Netlify            |
| GitHub Actions Cron        | Free hoàn toàn, không cần server riêng, đủ cho scheduler    | Vercel Cron (Pro)  |
| openpyxl                   | Nhẹ, format Excel đẹp                                       | xlsxwriter         |
| **Không dùng Redis**       | QR token store thẳng vào Supabase đủ dùng cho <50 người     | —                  |
| **Không dùng APScheduler** | Chuyển sang GH Actions Cron, không cần long-running process | —                  |

---

## 5. Mini App — Pyng (Telegram Web App)

### Tên & Branding

|                    |                                      |
| ------------------ | ------------------------------------ |
| **Tên app**        | **Pyng**                             |
| **Tagline**        | "Ping your presence"                 |
| **Màu chủ đạo**    | `#FC3C44` — Apple Music Red          |
| **Background**     | `#161618` — Dark (Apple Music style) |
| **Surface / Card** | `#1C1C1E`                            |
| **Text chính**     | `#F5F5F7`                            |
| **Text phụ**       | `#636366`                            |
| **Font**           | `-apple-system` / Inter              |
| **Border radius**  | 12–20px (tròn, hiện đại)             |

### Design tokens

```css
:root {
  --pyng-red: #fc3c44; /* Primary — CTA, icon active, accent */
  --pyng-red-dim: #fc3c4420; /* Background tint nhẹ */
  --pyng-dark: #161618; /* App background */
  --pyng-card: #1c1c1e; /* Card, sheet, input background */
  --pyng-border: #38383a; /* Divider, border */
  --pyng-muted: #636366; /* Placeholder, secondary text */
  --pyng-white: #f5f5f7; /* Primary text */
  --pyng-green: #32d74b; /* Check-in success */
  --pyng-yellow: #ffd60a; /* Warning (late, quỹ muộn sắp hết) */
}
```

### Tech Stack

```
React 18 + TypeScript
Vite (build tool)
Tailwind CSS
@twa-dev/sdk (Telegram WebApp SDK)
React Query (data fetching)
Recharts (biểu đồ)
```

### Cài đặt Mini App

```bash
cd miniapp
npm install
npm run dev
```

### Deploy Mini App

```bash
# Build
npm run build

# Deploy lên Vercel (free)
npx vercel --prod
```

### Đăng ký Mini App với BotFather

```
/mybots → Chọn bot → Bot Settings → Menu Button
→ Nhập URL của Mini App
→ Nhập tên nút: "Dashboard"
```

---

## 6. QR Display — Client-side Polling

Không cần server riêng để refresh QR. Trang QR display là một **static page trên Vercel**
tự gọi API Supabase mỗi 60 giây để lấy token mới:

```html
<!-- /qr/index.html — deploy lên Vercel cùng Mini App -->
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <title>Pyng — BSMlabs Check-in</title>
    <style>
      /* Pyng brand colors — lấy cảm hứng từ Apple Music */
      :root {
        --pyng-red: #fc3c44; /* Apple Music primary — màu chủ đạo Pyng */
        --pyng-dark: #161618; /* Background tối như Apple Music */
        --pyng-card: #1c1c1e; /* Card surface */
        --pyng-muted: #636366; /* Text phụ */
        --pyng-white: #f5f5f7; /* Text chính */
      }
      * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }
      body {
        background: var(--pyng-dark);
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
        flex-direction: column;
        font-family: -apple-system, "Inter", sans-serif;
      }
      .logo {
        color: var(--pyng-red);
        font-size: 22px;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin-bottom: 28px;
      }
      img {
        width: 360px;
        border-radius: 20px;
        box-shadow: 0 0 80px #fc3c4430;
        border: 1px solid #ffffff10;
      }
      .timer {
        color: var(--pyng-white);
        font-size: 32px;
        font-weight: 700;
        margin-top: 20px;
      }
      .timer span {
        color: var(--pyng-red);
      }
      .office {
        color: var(--pyng-muted);
        margin-top: 8px;
        font-size: 13px;
      }
      .label {
        color: var(--pyng-muted);
        font-size: 11px;
        margin-top: 4px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }
    </style>
  </head>
  <body>
    <div class="logo">pyng</div>
    <img id="qr" src="" alt="QR Code" />
    <div class="office">📍 BSMlabs — 219 Trung Kính, Cầu Giấy, Hà Nội</div>
    <div class="timer"><span id="countdown">60</span>s</div>
    <div class="label">Mã QR tự động đổi mới</div>

    <script>
      const SUPABASE_URL = "https://xxxx.supabase.co";
      const SUPABASE_ANON_KEY = "your_anon_key";
      const QR_API = "/api/qr/current"; // Vercel function trả về base64 QR image

      let count = 60;

      async function refreshQR() {
        const res = await fetch(QR_API);
        const data = await res.json();
        document.getElementById("qr").src =
          `data:image/png;base64,${data.qr_base64}`;
        count = 60;
      }

      setInterval(() => {
        count--;
        document.getElementById("countdown").textContent = count;
        if (count <= 0) refreshQR();
      }, 1000);

      refreshQR(); // Load ngay khi mở trang
    </script>
  </body>
</html>
```

**Vercel Function `/api/qr/current`** — generate QR từ token trong Supabase:

```python
# api/qr/current.py (Vercel Serverless)
def handler(request, response):
    token = get_latest_qr_token_from_supabase()  # Query Supabase
    qr_image = generate_qr(token)                # qrcode + Pillow
    return response.json({"qr_base64": to_base64(qr_image)})
```

> 💡 **Lợi ích**: Không cần server long-running. QR page chạy hoàn toàn trên
> Vercel free tier. Token được generate và lưu vào Supabase bởi GitHub Actions
> cron mỗi phút trong giờ làm việc.

---

## 7. NFC Tag Setup — BSMlabs

### Phần cứng cần mua

- **NFC Tag**: NTAG213 hoặc NTAG215 (mua trên Shopee ~5.000–10.000đ/cái)
- **App ghi NFC**: NFC Tools (Android) hoặc NFC TagWriter by NXP

### Nội dung ghi vào tag

```
URL: https://t.me/PyngBot?start=nfc_BSMLABS_MAIN_DOOR
```

### Cách ghi tag

1. Mở NFC Tools trên Android
2. Chọn "Write" → "Add a record" → "URL"
3. Nhập URL của bot
4. Đặt điện thoại lên tag → Ghi

### Vị trí dán tag — 219 Trung Kính

- Cạnh cửa vào văn phòng BSMlabs, ngang tầm tay (~1.2m)
- Tránh gần khung cửa kim loại (dùng anti-metal tag nếu cần)
- Dán thêm 1 tag dự phòng ở bên trong cửa

---

## 8. Chi phí hàng tháng — BSMlabs (<50 nhân viên)

| Dịch vụ            | Dùng cho                           | Chi phí                                  |
| ------------------ | ---------------------------------- | ---------------------------------------- |
| **Vercel**         | Bot webhook + Mini App + QR page   | ✅ Free                                  |
| **Supabase**       | PostgreSQL + QR token store        | ✅ Free (500MB, đủ dùng nhiều năm)       |
| **GitHub Actions** | Cron scheduler (nhắc, báo cáo, QR) | ✅ Free (2000 phút/tháng, dùng ~50 phút) |
| **NFC Tags**       | 5–10 cái (mua 1 lần)               | ~50.000đ một lần                         |
| Face++ (optional)  | Xác minh selfie manual check-in    | ✅ Free (1000 calls/tháng)               |

**Tổng chi phí hàng tháng: $0** 🎉

> Chỉ phát sinh chi phí nếu: Supabase vượt 500MB (nâng $25/tháng),
> hoặc cần domain riêng (~$10/năm).
