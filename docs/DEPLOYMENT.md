# DEPLOYMENT.md — Hướng dẫn Deploy

**Stack**: Vercel (Bot + Mini App) + Supabase (DB) + GitHub Actions (Cron)  
**Chi phí**: $0/tháng

---

## 1. Chuẩn bị trước khi deploy

### 1.1 Tạo Telegram Bot

```
1. Mở Telegram, tìm @BotFather
2. Gửi /newbot
3. Đặt tên: "Pyng"
4. Đặt username: PyngBot (hoặc tên app đã chọn)
5. Lưu lại BOT_TOKEN được cấp
```

### 1.2 Supabase — bạn đã có account

```
1. Tạo project mới: "pyng"
2. Region: Southeast Asia (Singapore) — gần Hà Nội nhất
3. Settings → Database → lấy Connection string (Transaction pooler)
4. Settings → API → lấy URL, anon key, service_role key
5. SQL Editor → chạy toàn bộ schema (xem ARCHITECTURE.md)
6. Seed system_config với giá trị BSMlabs (xem mục 6 bên dưới)
```

### 1.3 GitHub Repository

```bash
# Tạo repo, push code lên
git init
git remote add origin https://github.com/bsmlabs/checkin-bot
git push -u origin main
```

---

## 2. Deploy Bot lên Vercel

Bot chạy dưới dạng **Serverless Functions** — mỗi request là một function invocation.

### 2.1 Cấu trúc thư mục Vercel

```
/
├── api/
│   ├── webhook.py        ← Nhận update từ Telegram
│   ├── cron/
│   │   ├── morning.py    ← GitHub Actions gọi vào
│   │   ├── evening.py
│   │   ├── report.py
│   │   └── qr_refresh.py
│   └── qr/
│       └── current.py    ← QR display page fetch
├── miniapp/              ← React Mini App
├── qr/
│   └── index.html        ← QR display page
├── vercel.json
└── requirements.txt
```

### 2.2 `vercel.json`

```json
{
  "functions": {
    "api/**/*.py": {
      "runtime": "python3.11"
    }
  },
  "routes": [
    { "src": "/api/(.*)", "dest": "/api/$1" },
    { "src": "/qr", "dest": "/qr/index.html" },
    { "src": "/(.*)", "dest": "/miniapp/$1" }
  ]
}
```

### 2.3 Deploy lên Vercel

```bash
# Cài Vercel CLI (bạn đã quen)
npm install -g vercel

# Login và deploy
vercel login
vercel --prod

# Lấy URL, ví dụ: https://pyng.vercel.app
```

Hoặc connect GitHub → Vercel tự deploy khi push `main`.

### 2.4 Thêm Environment Variables trên Vercel Dashboard

```
Vercel Dashboard → Project → Settings → Environment Variables
→ Add từng biến từ .env.example (xem TECH_STACK.md)

Quan trọng nhất:
- TELEGRAM_BOT_TOKEN
- DATABASE_URL
- SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY
- CRON_SECRET
- JWT_SECRET
```

### 2.5 Set Webhook Telegram

```bash
# Sau khi có Vercel URL, set webhook
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://pyng.vercel.app/api/webhook",
    "allowed_updates": ["message", "callback_query"]
  }'

# Verify
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo"
# → "url" phải đúng, "last_error_message" phải trống
```

---

## 3. Setup GitHub Actions — Cron Scheduler

Đây là phần **thay thế hoàn toàn cho APScheduler + Railway**.  
Tạo các file trong `.github/workflows/`:

### 3.1 Nhắc check-in buổi sáng — 8:30 AM (T2–T6)

```yaml
# .github/workflows/remind_morning.yml
name: Morning Check-in Reminder

on:
  schedule:
    - cron: "30 1 * * 1-5" # 8:30 AM ICT = 01:30 UTC

jobs:
  remind:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger morning reminder
        run: |
          curl -X POST https://pyng.vercel.app/api/cron/morning \
            -H "Authorization: Bearer ${{ secrets.CRON_SECRET }}" \
            -H "Content-Type: application/json"
```

### 3.2 Nhắc check-out buổi chiều — 17:45 PM (T2–T6)

```yaml
# .github/workflows/remind_evening.yml
name: Evening Check-out Reminder

on:
  schedule:
    - cron: "45 10 * * 1-5" # 17:45 ICT = 10:45 UTC

jobs:
  remind:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger evening reminder
        run: |
          curl -X POST https://pyng.vercel.app/api/cron/evening \
            -H "Authorization: Bearer ${{ secrets.CRON_SECRET }}"
```

### 3.3 Báo cáo hàng ngày — 9:15 AM (T2–T6)

```yaml
# .github/workflows/daily_report.yml
name: Daily Attendance Report

on:
  schedule:
    - cron: "15 2 * * 1-5" # 9:15 AM ICT = 02:15 UTC

jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - name: Send daily report to HR group
        run: |
          curl -X POST https://pyng.vercel.app/api/cron/report \
            -H "Authorization: Bearer ${{ secrets.CRON_SECRET }}"
```

### 3.4 Refresh QR Token — Mỗi phút trong giờ làm việc

```yaml
# .github/workflows/qr_refresh.yml
name: QR Token Refresh

on:
  schedule:
    # Mỗi phút từ 8:00–18:00 ICT (1:00–11:00 UTC) — T2-T6
    # GitHub Actions tối thiểu mỗi 5 phút, dùng kết hợp với QR expire 5 phút
    - cron: "*/5 1-11 * * 1-5"

jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - name: Refresh QR token in Supabase
        run: |
          curl -X POST https://pyng.vercel.app/api/cron/qr_refresh \
            -H "Authorization: Bearer ${{ secrets.CRON_SECRET }}"
```

> ⚠️ **Lưu ý**: GitHub Actions cron tối thiểu là **5 phút**, không thể mỗi 30 giây.  
> Giải pháp: Set QR expire = **5 phút** (đủ an toàn cho văn phòng nhỏ) hoặc
> dùng client-side generation (xem TECH_STACK.md §6).

### 3.5 Auto check-out — 23:59 hàng ngày

```yaml
# .github/workflows/auto_checkout.yml
name: Auto Checkout

on:
  schedule:
    - cron: "59 16 * * 1-5" # 23:59 ICT = 16:59 UTC

jobs:
  checkout:
    runs-on: ubuntu-latest
    steps:
      - name: Auto checkout users who forgot
        run: |
          curl -X POST https://pyng.vercel.app/api/cron/auto_checkout \
            -H "Authorization: Bearer ${{ secrets.CRON_SECRET }}"
```

### 3.6 Thêm CRON_SECRET vào GitHub Secrets

```
GitHub Repo → Settings → Secrets and variables → Actions
→ New repository secret
→ Name: CRON_SECRET
→ Value: [chuỗi random, giống với CRON_SECRET trong Vercel env]
```

---

## 4. Khởi tạo Database (BSMlabs config)

```bash
# Chạy schema SQL trên Supabase SQL Editor
# (copy từ ARCHITECTURE.md → Database Schema)

# Sau đó seed config BSMlabs
INSERT INTO system_config VALUES
  ('office_name',          'BSMlabs Office',                    NULL, NOW()),
  ('office_address',       '219 Trung Kính, Yên Hòa, Cầu Giấy, Hà Nội', NULL, NOW()),
  ('timezone',             'Asia/Ho_Chi_Minh',                  NULL, NOW()),
  ('work_start_time',      '08:45',                             NULL, NOW()),
  ('work_end_time',        '17:45',                             NULL, NOW()),
  ('checkin_remind_time',  '08:30',                             NULL, NOW()),
  ('checkout_remind_time', '17:45',                             NULL, NOW()),
  ('daily_report_time',    '09:15',                             NULL, NOW()),
  ('late_budget_minutes',  '180',                               NULL, NOW()),  -- 3 tiếng
  ('late_grace_minutes',   '5',                                 NULL, NOW()),
  ('wfh_limit_per_month',  '2',                                 NULL, NOW()),
  ('qr_expire_seconds',    '300',                               NULL, NOW()),  -- 5 phút
  ('auto_checkout_time',   '23:59',                             NULL, NOW());

-- Thêm văn phòng BSMlabs
INSERT INTO offices (name, latitude, longitude, radius_m) VALUES
  ('BSMlabs — 219 Trung Kính', 21.0285, 105.7968, 120);

-- Thêm WiFi whitelist
INSERT INTO wifi_whitelist (office_id, ssid, description) VALUES
  (1, 'BSMlabs_WiFi', 'WiFi chính văn phòng'),
  (1, 'BSMlabs_5G',   'WiFi 5GHz văn phòng');
```

---

## 5. Deploy Mini App lên Vercel

Mini App được deploy cùng repo (monorepo) hoặc repo riêng:

```bash
cd miniapp
npm install
npm run build

# Nếu deploy riêng
vercel --prod
# URL: https://pyng-app.vercel.app
```

### Đăng ký Menu Button với BotFather

```
/mybots → @PyngBot → Bot Settings → Menu Button
→ Edit URL: https://pyng.vercel.app
→ Edit Text: 📊 Dashboard
```

---

## 6. Setup NFC Tags — BSMlabs

```
1. Vào bot: /admin → Cài đặt văn phòng → NFC Settings → Tạo tag mới
2. Bot tạo: URL = https://t.me/PyngBot?start=nfc_BSMLABS_abc123
3. Ghi URL vào NFC tag bằng NFC Tools (Android)
4. Dán cạnh cửa văn phòng 219 Trung Kính (ngang tầm tay, tránh khung kim loại)
5. Mua 5–10 tag NTAG215 trên Shopee (~50.000đ)
```

---

## 7. QR Display — 219 Trung Kính

```
URL: https://pyng.vercel.app/qr

Hiển thị trên:
- TV hoặc màn hình ở lối vào văn phòng
- Tablet dán tường cạnh cửa
- Laptop lễ tân (nếu có)

Trang tự fetch QR mới từ Supabase mỗi 5 phút.
Không cần kết nối đặc biệt, chỉ cần browser + internet.
```

---

## 8. Checklist Go-live — BSMlabs

```
PRE-LAUNCH:
□ Bot @PyngBot đã tạo và có token
□ Webhook set → https://pyng.vercel.app/api/webhook
□ getWebhookInfo trả về url đúng, không có error
□ Supabase schema đã chạy, seed data BSMlabs đã insert
□ Tọa độ 219 Trung Kính đã verify thực tế (đứng tại VP, check GPS)
□ WiFi SSID đã đúng (hỏi IT)
□ Tất cả GitHub Actions workflows đã enable
□ CRON_SECRET khớp giữa GitHub Secrets và Vercel env
□ Test cron bằng cách trigger thủ công (Actions → Run workflow)
□ QR display page mở được, QR hiển thị
□ NFC tag đã ghi và dán, test chạm thử
□ Mini App mở được từ bot (menu button)
□ Admin Telegram ID đã config đúng

LAUNCH:
□ Gửi link bot cho toàn bộ nhân viên BSMlabs
□ Gửi USAGE.md hoặc tóm tắt cho nhân viên
□ Admin duyệt đăng ký
□ Test check-in thử 3–5 người, cả 4 phương thức
□ Xác nhận báo cáo sáng hôm sau gửi đúng group HR

POST-LAUNCH (tuần 1):
□ Theo dõi Vercel Function logs hàng ngày
□ Kiểm tra GitHub Actions runs (xanh hết chưa?)
□ Khảo sát nhân viên sau 3 ngày
□ Điều chỉnh geofence radius nếu GPS hay bị false negative
```

---

## 9. Monitoring & Health Check

### 9.1 Logs

```bash
# Vercel Function logs (real-time)
vercel logs --follow

# Hoặc xem trên Vercel Dashboard → Project → Functions tab

# Webhook health check
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo"

# GitHub Actions: xem tại
# github.com/nsongha/Pyng/actions
```

### 9.2 Uptime Monitoring (Free)

Dùng [UptimeRobot](https://uptimerobot.com) (free 50 monitors):

```
1. Tạo account UptimeRobot
2. Add monitor:
   - Type: HTTP(s)
   - URL: https://pyng.vercel.app/api/webhook
   - Interval: 5 phút
   - Alert: Email khi down
3. Optional: thêm monitor cho Supabase health
   - URL: https://<supabase-project>.supabase.co/rest/v1/
   - Header: apikey=<anon_key>
```

### 9.3 Monitoring Checklist (hàng tuần)

```
□ Vercel Dashboard: function errors = 0?
□ GitHub Actions: tất cả cron runs xanh?
□ Supabase Dashboard: database size < 400MB? (free tier = 500MB)
□ getWebhookInfo: last_error_message trống?
□ UptimeRobot: uptime > 99%?
```

### 9.4 Alert Channels

| Alert type                 | Kênh                         |
| -------------------------- | ---------------------------- |
| Bot down                   | UptimeRobot → Email          |
| Cron fail                  | GitHub Actions email → admin |
| Supabase approaching limit | Supabase Dashboard email     |
| Deploy fail                | Vercel email notification    |

---

## 10. Incident Response & Rollback

### 10.1 Khi phát hiện bot không phản hồi

```
1. Verify: curl "https://api.telegram.org/bot${TOKEN}/getWebhookInfo"
   → Nếu last_error_message có lỗi → xem bước 2
   → Nếu URL sai/trống → set lại webhook (mục 2.5)

2. Check Vercel logs:
   vercel logs --follow
   → Nếu có lỗi import/syntax → rollback (bước 10.2)
   → Nếu timeout → check Supabase (bước 3)

3. Check Supabase status:
   → Dashboard → Project paused? → Resume project
   → Database đầy? → Cleanup old records

4. Check env vars:
   → Vercel Dashboard → Settings → Environment Variables
   → Tất cả vars vẫn đúng? Token chưa bị revoke?
```

### 10.2 Rollback Vercel deployment

```bash
# Cách 1: CLI
vercel rollback

# Cách 2: Dashboard
# Vercel Dashboard → Deployments → chọn version OK → "..." → Promote to Production

# Cách 3: Git revert
git revert HEAD
git push origin main    # Vercel auto deploy
```

### 10.3 Recovery database

```bash
# Nếu có backup (xem mục 11)
# Restore từ SQL dump
psql $DATABASE_URL < backup_YYYYMMDD.sql

# Nếu chạy nhầm migration
# Revert thủ công: viết reverse SQL trên Supabase SQL Editor
```

### 10.4 Common failures & fixes

| Triệu chứng                 | Nguyên nhân thường gặp             | Fix                                      |
| --------------------------- | ---------------------------------- | ---------------------------------------- |
| Bot im lặng                 | Webhook URL sai hoặc Vercel down   | Set lại webhook, check Vercel status     |
| "Internal Server Error" 500 | Import error, env var thiếu        | Check logs, rollback, verify env vars    |
| Cron không chạy             | GitHub Actions disabled / paused   | Repo → Actions → Enable, re-run manually |
| QR page trắng               | Supabase paused hoặc API key sai   | Resume project, check SUPABASE_URL       |
| Check-in fail "DB error"    | Supabase free tier paused (7 ngày) | Resume project, setup keepalive ping     |

---

## 11. Database Backup & Recovery

> ⚠️ Supabase free tier **KHÔNG có** point-in-time recovery.
> Nếu data bị mất/corruption → chỉ recover được từ manual backup.

### 11.1 Manual backup (chạy định kỳ)

```bash
# Cần Supabase CLI và DATABASE_URL
# Dump toàn bộ schema + data
supabase db dump --data-only -f backup_$(date +%Y%m%d).sql

# Hoặc dùng pg_dump nếu có DATABASE_URL
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

### 11.2 Backup schedule

| Tần suất        | Nội dung    | Lưu ở đâu                  |
| --------------- | ----------- | -------------------------- |
| Hàng tuần       | Full dump   | Local hoặc Google Drive    |
| Trước deploy    | Schema only | Commit vào repo (nếu khác) |
| Trước migration | Full dump   | Local, giữ 30 ngày         |

### 11.3 Recovery steps

```
1. Lấy file backup gần nhất
2. Supabase SQL Editor → paste nội dung backup
3. Hoặc: psql $DATABASE_URL < backup_YYYYMMDD.sql
4. Verify: query users, checkins → data đúng
5. Test bot: gửi /start → bot phản hồi đúng
```

### 11.4 Lưu ý quan trọng

- **LUÔN backup TRƯỚC KHI chạy migration mới**
- Free tier giới hạn 500MB — monitor trên Supabase Dashboard
- Giữ ít nhất 4 bản backup gần nhất (1 tháng)
- Khi upgrade Pro ($25/tháng): bật point-in-time recovery tự động
