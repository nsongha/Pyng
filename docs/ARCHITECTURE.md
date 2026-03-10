# ARCHITECTURE.md — Thiết kế hệ thống

---

## 1. Kiến trúc tổng thể

```
┌─────────────────────────────────────────────────────────┐
│                      CLIENTS                             │
│  Telegram App (iOS/Android/Desktop)  │  QR Display Page │
└───────────────────┬─────────────────────────┬───────────┘
                    │ HTTPS Webhook            │ Browser
                    ▼                          ▼
┌─────────────────────────────────────────────────────────┐
│              VERCEL SERVERLESS FUNCTIONS                  │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │ api/webhook │  │  qr/display  │  │  Mini App API  │ │
│  │   .py       │  │  (static)    │  │   (REST)       │ │
│  └──────┬──────┘  └──────┬───────┘  └───────┬────────┘ │
│         │                │                   │          │
│         ▼                ▼                   ▼          │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Core Bot Engine                     │   │
│  │                                                  │   │
│  │  ┌─────────────┐    ┌──────────────────────┐    │   │
│  │  │  Handlers   │    │     Validators        │    │   │
│  │  │  - checkin  │    │  - GPS Geofence       │    │   │
│  │  │  - admin    │    │  - WiFi Whitelist     │    │   │
│  │  │  - report   │    │  - QR Token           │    │   │
│  │  │  - register │    │  - NFC Token          │    │   │
│  │  │  - leave    │    └──────────────────────┘    │   │
│  │  └─────────────┘                                 │   │
│  │                      ┌──────────────────────┐    │   │
│  │                      │      Services         │    │   │
│  │                      │  - Gamification       │    │   │
│  │                      │  - Report Generator   │    │   │
│  │                      │  - Notification       │    │   │
│  │                      └──────────────────────┘    │   │
│  └─────────────────────────────────────────────────┘   │
│                          │                               │
└──────────────────────────┼──────────────────────────────┘
                           │
                           ▼
              ┌───────────────────────────┐
              │  PostgreSQL (Supabase)    │
              │  + QR token store         │
              └───────────────────────────┘

GitHub Actions (Cron) → gọi Vercel endpoints:
  ├── 08:30 → /api/cron/morning
  ├── 17:45 → /api/cron/evening
  ├── 09:15 → /api/cron/report
  ├── */5   → /api/cron/qr_refresh
  └── 23:59 → /api/cron/auto_checkout
```

---

## 2. Database Schema

### Bảng `users`

```sql
CREATE TABLE users (
    id              SERIAL PRIMARY KEY,
    telegram_id     BIGINT UNIQUE NOT NULL,
    telegram_username VARCHAR(100),
    full_name       VARCHAR(200) NOT NULL,
    email           VARCHAR(200) UNIQUE,
    role            VARCHAR(20) DEFAULT 'employee',  -- employee | manager | admin
    department      VARCHAR(100),
    is_active       BOOLEAN DEFAULT TRUE,
    registered_at   TIMESTAMP DEFAULT NOW(),
    face_photo_url  VARCHAR(500),   -- optional, Face++ enrolled
    annual_leave_days INT DEFAULT 12
);
```

### Bảng `offices`

```sql
CREATE TABLE offices (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(200) NOT NULL,          -- "Văn phòng HCM", "Chi nhánh HN"
    latitude    DECIMAL(10, 8) NOT NULL,
    longitude   DECIMAL(11, 8) NOT NULL,
    radius_m    INT DEFAULT 100,                -- bán kính tính bằng mét
    is_active   BOOLEAN DEFAULT TRUE,
    created_by  BIGINT REFERENCES users(telegram_id),
    created_at  TIMESTAMP DEFAULT NOW()
);
```

### Bảng `wifi_whitelist`

```sql
CREATE TABLE wifi_whitelist (
    id          SERIAL PRIMARY KEY,
    office_id   INT REFERENCES offices(id),
    ssid        VARCHAR(200) NOT NULL,           -- tên WiFi
    description VARCHAR(200),                   -- "Tầng 2 - Phòng họp"
    is_active   BOOLEAN DEFAULT TRUE,
    added_by    BIGINT REFERENCES users(telegram_id),
    added_at    TIMESTAMP DEFAULT NOW()
);
```

### Bảng `nfc_tokens`

```sql
CREATE TABLE nfc_tokens (
    id          SERIAL PRIMARY KEY,
    token       VARCHAR(100) UNIQUE NOT NULL,
    office_id   INT REFERENCES offices(id),
    location    VARCHAR(200),                   -- "Cửa chính", "Cửa phụ"
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW()
);
```

### Bảng `qr_sessions`

```sql
CREATE TABLE qr_sessions (
    id          SERIAL PRIMARY KEY,
    token       VARCHAR(100) UNIQUE NOT NULL,
    office_id   INT REFERENCES offices(id),
    created_at  TIMESTAMP DEFAULT NOW(),
    expire_at   TIMESTAMP NOT NULL,             -- created_at + 30s
    is_used     BOOLEAN DEFAULT FALSE
);
-- Index cho cleanup
CREATE INDEX idx_qr_expire ON qr_sessions(expire_at);
```

### Bảng `checkins`

```sql
CREATE TABLE checkins (
    id              SERIAL PRIMARY KEY,
    user_id         INT REFERENCES users(id),
    type            VARCHAR(10) NOT NULL,        -- 'in' | 'out'
    method          VARCHAR(20) NOT NULL,        -- 'gps' | 'wifi' | 'qr' | 'nfc' | 'manual'
    office_id       INT REFERENCES offices(id),

    -- GPS fields
    latitude        DECIMAL(10, 8),
    longitude       DECIMAL(11, 8),
    gps_accuracy_m  INT,                        -- độ chính xác GPS (mét)
    distance_m      INT,                        -- khoảng cách đến văn phòng

    -- Meta
    wifi_ssid       VARCHAR(200),               -- nếu method = wifi
    is_valid        BOOLEAN DEFAULT TRUE,
    is_manual_approved BOOLEAN,                 -- nếu method = manual
    approved_by     BIGINT,                     -- telegram_id của admin duyệt

    -- Mood
    mood            VARCHAR(20),                -- 'great' | 'good' | 'tired' | 'sos'
    note            TEXT,

    -- Timestamps
    checked_at      TIMESTAMP DEFAULT NOW(),
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Index cho queries thường dùng
CREATE INDEX idx_checkins_user_date ON checkins(user_id, checked_at);
CREATE INDEX idx_checkins_date ON checkins(checked_at);
```

### Bảng `leaves`

```sql
CREATE TABLE leaves (
    id              SERIAL PRIMARY KEY,
    user_id         INT REFERENCES users(id),
    leave_type      VARCHAR(30) NOT NULL,       -- 'annual' | 'compensatory' | 'unpaid' | 'sick'
    start_date      DATE NOT NULL,
    end_date        DATE NOT NULL,
    days_count      DECIMAL(4,1),               -- hỗ trợ nửa ngày
    reason          TEXT,
    status          VARCHAR(20) DEFAULT 'pending', -- pending | approved | rejected
    approved_by     INT REFERENCES users(id),
    requested_at    TIMESTAMP DEFAULT NOW(),
    processed_at    TIMESTAMP
);
```

### Bảng `gamification`

```sql
CREATE TABLE gamification (
    id              SERIAL PRIMARY KEY,
    user_id         INT REFERENCES users(id) UNIQUE,
    total_points    INT DEFAULT 0,
    current_streak  INT DEFAULT 0,              -- streak ngày hiện tại
    longest_streak  INT DEFAULT 0,
    ontime_count    INT DEFAULT 0,              -- số lần đúng giờ
    early_count     INT DEFAULT 0,              -- số lần đến sớm
    updated_at      TIMESTAMP DEFAULT NOW()
);
```

### Bảng `point_transactions`

```sql
CREATE TABLE point_transactions (
    id          SERIAL PRIMARY KEY,
    user_id     INT REFERENCES users(id),
    points      INT NOT NULL,                   -- dương = cộng, âm = trừ
    reason      VARCHAR(100),                   -- 'daily_checkin' | 'streak_bonus' | 'early_bird'
    created_at  TIMESTAMP DEFAULT NOW()
);
```

### Bảng `system_config`

```sql
CREATE TABLE system_config (
    key         VARCHAR(100) PRIMARY KEY,
    value       TEXT NOT NULL,
    updated_by  BIGINT,
    updated_at  TIMESTAMP DEFAULT NOW()
);
```

> 📌 **Seed data** (BSMlabs config) → xem [DEPLOYMENT.md §4](./DEPLOYMENT.md#4-khởi-tạo-database-bsmlabs-config)

---

## 3. Luồng xử lý Check-in

```
User gửi check-in request
        │
        ▼
  Xác định method?
  ┌─────┬──────┬─────┬────────┐
  GPS  WiFi   QR   NFC   Manual
  │     │      │    │       │
  ▼     ▼      ▼    ▼       ▼
Validate theo method tương ứng
        │
   Valid?
   ├─ YES ──► Lưu checkin DB
   │               │
   │          Cập nhật Gamification
   │               │
   │          Gửi response đẹp kèm stats
   │               │
   │          Hỏi Mood (nếu check-in sáng)
   │
   └─ NO ──► Gợi ý method khác
              (fallback cascade)
```

### Fallback Cascade

```
GPS fail → thử WiFi → thử QR → thử NFC → Manual (selfie)
```

---

## 4. API Endpoints (Mini App)

```
GET  /api/me                    # Thông tin cá nhân + stats
GET  /api/checkins?month=2026-03 # Lịch sử check-in
GET  /api/team/today            # Trạng thái team hôm nay
GET  /api/leaderboard           # Bảng xếp hạng điểm
POST /api/leave/request         # Xin nghỉ
GET  /api/leave/my              # Danh sách nghỉ của tôi

# Admin only
GET  /api/admin/report/daily    # Báo cáo hàng ngày
GET  /api/admin/report/monthly  # Xuất Excel tháng
POST /api/admin/office          # Thêm văn phòng
PUT  /api/admin/office/:id      # Sửa geofence
POST /api/admin/wifi            # Thêm WiFi whitelist
POST /api/admin/nfc             # Tạo NFC token
POST /api/admin/approve/:id     # Duyệt check-in thủ công
```

---

## 5. QR Code System

```
┌─────────────┐     refresh mỗi 5 phút  ┌──────────────────┐
│  QR Display  │ ◄─── client-side poll ─  │  GitHub Actions   │
│  (Web page)  │      từ Supabase        │  Cron (*/5 min)  │
└──────┬──────┘                         └──────────────────┘
       │ User scan QR
       ▼
  Telegram opens deep link:
  tg://resolve?domain=bot&start=qr_TOKEN123
       │
       ▼
  Bot nhận /start qr_TOKEN123
       │
  Validate: token tồn tại? chưa used? chưa expired?
       │
  ✅ Valid → Check-in thành công
  ❌ Invalid → "QR đã hết hạn, quét lại"
```

---

## 6. NFC System

```
NFC Tag chứa URL:
  https://t.me/YourBot?start=nfc_OFFICE1_DOOR_MAIN

Khi chạm:
  Android → mở Telegram → gửi /start nfc_OFFICE1_DOOR_MAIN
  iOS 14+ → tương tự

Bot xử lý:
  Parse token → tìm trong nfc_tokens table
  Validate is_active → Check-in với method='nfc'
  Kết hợp GPS check nhẹ (optional, không bắt buộc)
```

---

## 7. Bảo mật

| Lớp  | Biện pháp                                                   |
| ---- | ----------------------------------------------------------- |
| Bot  | Chỉ xử lý update từ Telegram IP whitelist                   |
| GPS  | Phát hiện spoofing bằng speed check + accuracy threshold    |
| QR   | Token expire 30s, 1 lần dùng                                |
| NFC  | Token static nhưng kết hợp GPS soft check                   |
| WiFi | Đây là phương thức low-security, chỉ dùng cho convenience   |
| Data | Ảnh selfie xóa sau 30 ngày, location không lưu quá chi tiết |
| API  | JWT auth cho Mini App API                                   |
| DB   | RLS (Row Level Security) trên Supabase                      |
