# Phase 4 Task Board — Gamification & Polish (v0.4.0)

> 🎯 Mục tiêu: Trải nghiệm hoàn chỉnh — gamification (điểm, streak, leaderboard, mood), Telegram Mini App dashboard, sẵn sàng go-live
> Version target: v0.4.0

## Thuật ngữ

- **Stream**: Nhóm tasks theo domain/concern — mỗi stream chạy trong 1 conversation riêng
- **Wave**: Đợt chạy, gộp 1+ streams cùng execution order (sequential trước, parallel sau)

## Parallel Execution Strategy

Phase này có **20 tasks** chia **5 streams**, **3 waves** (2 tasks Mini App dời sang Phase 5):

| Stream                       | Domain                 | Scope                                              | Wave |
| ---------------------------- | ---------------------- | -------------------------------------------------- | ---- |
| 🏆 **Gamification Services** | Services               | `services/`                                        | 1    |
| 🎮 **Gamification Bot**      | Bot Handlers           | `bot/handlers/`, `bot/app.py`                      | 2    |
| ⚛️ **Mini App**               | React Frontend         | `miniapp/`, `vercel.json`                           | 2    |
| 🔌 **Mini App API**          | API Endpoints          | `api/`                                              | 2    |
| 🧪 **Testing & Launch**      | QA + Docs              | `docs/`, `.github/workflows/`                       | 3    |

**Execution order**:

1. Wave 1: 🏆 Gamification Services — tạo services mới (gamification_service, mood_service)
2. Wave 2: 🎮 Gamification Bot + ⚛️ Mini App + 🔌 Mini App API — song song (domains khác nhau)
3. Wave 3: 🧪 Testing & Launch — integration, edge cases, docs

> **Lý do 3 waves**: Bot handlers cần gamification_service sẵn sàng. Mini App cần API endpoints, nhưng API và Bot handlers không overlap → song song an toàn. Testing cuối cùng để verify toàn bộ.

---

## Context: Codebase Hiện Tại

### Tech Stack

- **Backend**: Python 3.11+ / python-telegram-bot v21.5 (async webhook)
- **Database**: Supabase PostgreSQL (PostgREST API qua httpx, KHÔNG dùng SDK)
- **Deploy**: Vercel Serverless (auto-deploy từ GitHub)
- **Scheduler**: GitHub Actions Cron
- **Frontend**: React 18 + Vite + Tailwind (chưa scaffold)
- **Version hiện tại**: v0.3.0 (Phase 3 hoàn thành)

### Foundation Available

- `db/client.py` — REST wrapper (select, insert, update, delete) qua PostgREST API
- `db/schema.sql` — Tables sẵn: `gamification` (user_id UNIQUE, total_points, current_streak, longest_streak, ontime_count, early_count), `point_transactions` (user_id, points, reason, created_at)
- `checkins` table — column `mood` (VARCHAR: 'great' | 'good' | 'tired' | 'sos') đã có nhưng chưa dùng
- `services/checkin_service.py` — `create_checkin()` (chưa set mood), `get_today_checkin()`, `create_checkout()`, `create_wfh_checkin()`
- `services/user_service.py` — `register_user()`, `get_by_telegram_id()`, `get_all_active_users()`, `get_all_users()`, `update_user()`
- `services/report_service.py` — daily/weekly/monthly reports + Excel
- `services/leave_service.py` — leave CRUD + business logic
- `services/config_service.py` — system_config CRUD
- `bot/handlers/_helpers.py` — `get_active_user_or_none()`, `get_ontime_status()`, `format_current_time()`
- `bot/handlers/checkin.py` — Re-export module, `get_checkin_handlers()`
- `bot/app.py` — Application factory, đăng ký handlers (88 lines)
- `config/settings.py` — Có sẵn: `JWT_SECRET`, `JWT_EXPIRE_HOURS`, `MINI_APP_URL`
- `vercel.json` — Có rewrite cho `/qr`, cần thêm cho miniapp
- `docs/GAMIFICATION_DESIGN.md` — Thiết kế đầy đủ: điểm, streak, badges, leaderboard, mood, rewards

### DB Schema sẵn có (quan trọng cho Phase 4)

```sql
-- Gamification (sẵn, chưa có service)
CREATE TABLE gamification (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) UNIQUE,
    total_points INT DEFAULT 0,
    current_streak INT DEFAULT 0,
    longest_streak INT DEFAULT 0,
    ontime_count INT DEFAULT 0,
    early_count INT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Point Transactions (sẵn, chưa có service)
CREATE TABLE point_transactions (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    points INT NOT NULL,
    reason VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Checkins.mood (sẵn, chưa dùng)
-- mood VARCHAR(20), -- 'great' | 'good' | 'tired' | 'sos'
```

### API Endpoints Available

| Method | Path                   | Mô tả                         |
| ------ | ---------------------- | ----------------------------- |
| POST   | `/api/webhook`         | Nhận Telegram webhook updates |
| POST   | `/api/cron/morning`    | Nhắc check-in 08:30           |
| POST   | `/api/cron/evening`    | Nhắc check-out 17:45          |
| POST   | `/api/cron/qr_refresh` | Refresh QR mỗi 5 phút         |
| POST   | `/api/cron/daily_report` | Báo cáo hàng ngày 9:15 AM   |
| GET    | `/api/qr/current`      | QR session hiện tại (JSON)    |

### Patterns cần tuân theo

1. **Handler pattern**: Mỗi handler file export hàm `get_xxx_handler()` hoặc `get_xxx_handlers()`
2. **Service pattern**: Business logic trong `services/`, KHÔNG trong handler
3. **DB pattern**: Dùng `db.client` (select/insert/update/delete), KHÔNG import httpx trực tiếp
4. **Admin check**: Dùng `ADMIN_TELEGRAM_IDS` hoặc kiểm tra `user["role"] == "admin"`
5. **Cron pattern**: Vercel serverless `class handler(BaseHTTPRequestHandler)`, `do_POST` verify CRON_SECRET, `do_GET` health check
6. **API pattern**: Vercel serverless function, JWT auth cho Mini App endpoints

---

## Stream 🏆 A — Gamification Services

**Owner**: Services
**Scope**: `services/gamification_service.py`, `services/mood_service.py`

| #   | Task                                    | Status | Priority | Dependencies | Files affected                          |
| --- | --------------------------------------- | ------ | -------- | ------------ | --------------------------------------- |
| A1  | Gamification Service (points + streak)  | ✅     | P0       | —            | `services/gamification_service.py` [NEW] |
| A2  | Mood Service (record + analytics)       | ✅     | P0       | —            | `services/mood_service.py` [NEW]        |
| A3  | Tích hợp auto-points vào checkin_service | ✅     | P0       | A1           | `services/checkin_service.py`           |

**Acceptance Criteria:**

- A1: CRUD cho bảng `gamification` + `point_transactions`.
  - `get_or_create_gamification(user_id)` → lấy hoặc tạo record gamification cho user
  - `add_points(user_id, points, reason)` → cộng điểm + tạo transaction + update total_points
  - `calculate_checkin_points(user_id, checkin_type, is_ontime, is_early, is_wfh)` → tính điểm theo GAMIFICATION_DESIGN.md (đúng giờ +10, sớm +15, muộn ≤30 +5, muộn >30 +2, WFH +8)
  - `update_streak(user_id, action)` → action='checkin' tăng streak + check milestone bonus, action='reset' reset về 0
  - `get_leaderboard(period='month', limit=10)` → top users theo total_points
  - `get_user_stats(user_id)` → {total_points, current_streak, longest_streak, rank, ontime_count, early_count}
  - `check_streak_milestones(current_streak)` → trả về bonus points nếu đạt milestone (5→+20, 10→+50, 20→+100, 30→+200)
  - `is_first_checkin_today(user_id)` → check xem user có phải người đầu tiên check-in hôm nay không (+5 bonus)
- A2: Mood tracking service.
  - `record_mood(user_id, checkin_id, mood)` → update mood vào checkin record
  - `get_mood_stats(period='week')` → aggregate mood data (count by type, percentage)
  - `check_burnout_alert(user_id)` → kiểm tra 3 ngày liên tiếp 'sos' → return True/False
  - `get_user_mood_history(user_id, days=30)` → lịch sử mood 30 ngày
- A3: Sau mỗi check-in thành công → auto gọi `calculate_checkin_points()` + `update_streak()` + `add_points()`. Thêm parameter `mood` vào `create_checkin()`. KHÔNG thay đổi signature của functions hiện tại (backward compatible)

---

## Stream 🎮 B — Gamification Bot Handlers

**Owner**: Bot Handlers
**Scope**: `bot/handlers/gamification.py`, `bot/handlers/mood.py`, `bot/app.py`

| #   | Task                                    | Status | Priority | Dependencies | Files affected                          |
| --- | --------------------------------------- | ------ | -------- | ------------ | --------------------------------------- |
| B1  | Mood prompt sau check-in                | ✅     | P0       | A2, A3       | `bot/handlers/mood.py` [NEW]            |
| B2  | Leaderboard command (/leaderboard, /xh) | ✅     | P0       | A1           | `bot/handlers/gamification.py` [NEW]    |
| B3  | Stats/Points command (/points, /diem)   | ✅     | P0       | A1           | `bot/handlers/gamification.py`          |
| B4  | Streak display khi check-in             | ✅     | P1       | A1           | `bot/handlers/gamification.py`          |
| B5  | Burnout alert cho manager               | ✅     | P2       | A2           | `bot/handlers/mood.py`                  |
| B6  | Register gamification handlers          | ✅     | P0       | B1-B5        | `bot/app.py`                            |

**Acceptance Criteria:**

- B1: Sau check-in thành công (GPS/WiFi/QR/NFC), bot hỏi mood bằng inline keyboard: [🔥 Siêu năng suất] [😊 Bình thường] [😴 Hơi mệt] [🆘 Cần hỗ trợ]. Chỉ hỏi khi check-in sáng (type='in'), KHÔNG hỏi khi checkout/WFH. Callback data format: `mood_TYPE_CHECKINID`. Ghi mood vào record qua `mood_service.record_mood()`. Timeout 5 phút → tự bỏ qua
- B2: `/leaderboard` hoặc `/xh` → hiển thị top 10 tháng này (format theo GAMIFICATION_DESIGN.md §5.1). Hiển thị vị trí user hiện tại nếu không trong top 10. Chỉ active users
- B3: `/points` hoặc `/diem` → hiển thị: tổng điểm, streak hiện tại, longest streak, rank tháng, ontime count, early count. Hiển thị streak milestone icon (🔥, ⚡, 💎)
- B4: Khi check-in thành công, thêm dòng "🔥 Streak: N ngày | +X pts" vào message response. Nếu đạt milestone → hiển thị congratulations message
- B5: Tự động kiểm tra burnout (3 ngày 'sos' liên tiếp). Gửi cảnh báo cho admin/manager qua private message. Inline buttons: [💬 Nhắn tin ngay] [Bỏ qua]
- B6: Gamification + Mood handlers đăng ký trong `create_bot()`, KHÔNG conflict với handlers cũ

> ⚠️ **Mood callback data**: Dùng prefix `mood_` để tránh conflict với admin callbacks (`ap_*`, `approve_*`, `reject_*`, `leave_*`)

---

## Stream ⚛️ C — Mini App (React)

**Owner**: React Frontend
**Scope**: `miniapp/`, `vercel.json`

| #   | Task                                        | Status | Priority | Dependencies | Files affected              |
| --- | ------------------------------------------- | ------ | -------- | ------------ | --------------------------- |
| C1  | React project scaffold (Vite + Tailwind)     | ✅     | P0       | —            | `miniapp/` [NEW]            |
| C2  | Telegram WebApp SDK integration              | ✅     | P0       | C1           | `miniapp/src/`              |
| C3  | Dashboard: check-in history + stats          | ✅     | P0       | C1, C2       | `miniapp/src/pages/`        |
| C4  | Chart: working hours + attendance            | ➡️ Phase 5 | P1  | C3           | `miniapp/src/components/`   |
| C5  | Leave request form                           | ➡️ Phase 5 | P2  | C3           | `miniapp/src/pages/`        |
| C6  | Vercel config cho miniapp serving            | ✅     | P0       | C1           | `vercel.json`               |

**Acceptance Criteria:**

- C1: `npx create-vite-app` trong `miniapp/`. React 18 + TypeScript + Tailwind CSS v4. Package: `@twa-dev/sdk` cho Telegram WebApp API. Build output → `miniapp/dist/`. Development server `npm run dev --prefix miniapp`
- C2: Khởi tạo `WebApp.ready()`, back button, theme colors. Auth: `WebApp.initData` + validate bằng JWT_SECRET trên server. Lấy user info từ `WebApp.initDataUnsafe.user`
- C3: Trang chính: lịch sử check-in 30 ngày gần nhất (date, time in/out, method, status). Stats card: tổng ngày đi, muộn, WFH, nghỉ phép. Gamification card: điểm, streak, rank. Pull-to-refresh
- ~~C4: Dời sang Phase 5~~
- ~~C5: Dời sang Phase 5~~
- C6: Vercel rewrite: `/miniapp(.*)` → `miniapp/dist/index.html`. CSP header cho Mini App origin

> ⚠️ **Mini App auth pattern**: `WebApp.initData` → gửi lên API header → server validate bằng HMAC-SHA256 (dùng BOT_TOKEN). KHÔNG dùng Supabase Auth. Xem Telegram docs: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app

---

## Stream 🔌 D — Mini App API

**Owner**: API Endpoints
**Scope**: `api/me.py`, `api/checkins.py`, `api/leaderboard.py`, `api/leave/request.py`, `services/auth_service.py`

| #   | Task                                    | Status | Priority | Dependencies | Files affected                        |
| --- | --------------------------------------- | ------ | -------- | ------------ | ------------------------------------- |
| D1  | Auth Service (Telegram initData verify) | ✅     | P0       | —            | `services/auth_service.py` [NEW]      |
| D2  | GET /api/me (user info + stats)         | ✅     | P0       | D1, A1       | `api/me.py` [NEW]                     |
| D3  | GET /api/checkins (check-in history)    | ✅     | P0       | D1           | `api/checkins.py` [NEW]               |
| D4  | GET /api/leaderboard                    | ✅     | P1       | D1, A1       | `api/leaderboard.py` [NEW]            |

**Acceptance Criteria:**

- D1: `validate_telegram_init_data(init_data_str)` → verify HMAC-SHA256 theo Telegram docs. Trả về `{user_id, username, first_name, auth_date}` nếu valid. Middleware pattern: decorator `@require_auth` cho API endpoints. Dùng `TELEGRAM_BOT_TOKEN` để tạo secret key (HMAC-SHA256 với "WebAppData")
- D2: `GET /api/me` (auth required) → `{user, gamification, checkin_stats, leave_balance}`. User info + gamification stats + check-in summary tháng + remaining leave days
- D3: `GET /api/checkins?limit=30&offset=0` (auth required) → paginated check-in history. Mỗi record: date, time_in, time_out, method, mood, is_ontime
- D4: `GET /api/leaderboard?period=month` (auth required) → top 10 users + user's rank. Period: 'month' | 'alltime'

---

## Stream 🧪 E — Testing & Launch

**Owner**: QA + Docs
**Scope**: `docs/`, `.github/workflows/`

| #   | Task                                      | Status | Priority | Dependencies    | Files affected                            |
| --- | ----------------------------------------- | ------ | -------- | --------------- | ----------------------------------------- |
| E1  | Cron: weekly leaderboard + streak reminder | ✅     | P1       | A1              | `api/cron/weekly.py` [NEW], `.github/workflows/cron-reminders.yml` |
| E2  | Test toàn bộ flows (checklist)             | ✅     | P0       | Tất cả streams  | `docs/QC_REPORT.md`                      |
| E3  | Fix bugs từ testing                        | ✅     | P0       | E2              | `bot/handlers/_helpers.py`, `gps_checkin.py`, `wifi_checkin.py`, `qr_checkin.py`, `nfc_checkin.py`, `wfh.py`, `checkout.py` |

**Acceptance Criteria:**

- E1: Cron weekly (Monday 9:00 AM): gửi leaderboard tuần trước vào group + streak reminder cá nhân cho users có streak > 0. Cron format: `0 2 * * 1` (UTC) = 9:00 AM UTC+7 Monday
- E2: Chạy full test checklist theo `KNOWN_ISSUES.md` §📋. Test gamification flow end-to-end: check-in → mood → points → leaderboard. Test Mini App: mở trong Telegram → hiển thị data đúng
- E3: Fix tất cả P0 bugs phát hiện trong E2

---

## Cross-Stream Dependencies

### Dependency Map

| Task | Depends on | Type         | Notes                                          |
| ---- | ---------- | ------------ | ---------------------------------------------- |
| A3   | A1         | in-stream    | Auto-points cần gamification_service            |
| B1   | A2, A3     | cross-stream | Mood prompt cần mood_service + checkin flow     |
| B2   | A1         | cross-stream | Leaderboard command cần gamification_service    |
| B3   | A1         | cross-stream | Points display cần gamification_service         |
| B4   | A1         | cross-stream | Streak display cần gamification_service         |
| B5   | A2         | cross-stream | Burnout alert cần mood_service                  |
| D2   | D1, A1     | cross-stream | /api/me cần auth + gamification stats            |
| D3   | D1         | in-stream    | /api/checkins cần auth service                   |
| D4   | D1, A1     | cross-stream | /api/leaderboard cần auth + gamification         |
| E1   | A1         | cross-stream | Weekly cron cần gamification_service             |
| E2   | All        | cross-stream | Testing cần tất cả xong                          |

### Execution Order

1. **Wave 1** (Sequential ⛓️): 🏆 Stream A — Gamification Services (foundation cho tất cả)
2. **Wave 2** (Parallel 🔀): 🎮 Stream B (Bot Handlers) + ⚛️ Stream C (Mini App) + 🔌 Stream D (API) — independent domains
3. **Wave 3** (Sequential ⛓️): 🧪 Stream E — Testing & Launch

---

## Conflict Prevention Rules

### Shared Files

| File                                   | Streams dùng        | Tasks      | Rule                                                                    |
| -------------------------------------- | -------------------- | ---------- | ----------------------------------------------------------------------- |
| `bot/app.py`                           | 🎮 B                | B6         | Chỉ Stream 🎮 sửa (thêm gamification + mood handler registrations)      |
| `services/checkin_service.py`          | 🏆 A                | A3         | Chỉ Stream 🏆 sửa ở Wave 1 (thêm auto-points integration)              |
| `vercel.json`                          | ⚛️ C                 | C6         | Chỉ Stream ⚛️ sửa (thêm miniapp rewrite rules)                          |
| `.github/workflows/cron-reminders.yml` | 🧪 E                | E1         | Chỉ Stream 🧪 sửa ở Wave 3                                              |
| `config/settings.py`                   | KHÔNG SỬA            | —          | Chỉ đọc, đã có JWT_SECRET, MINI_APP_URL                                 |
| `bot/handlers/admin.py`               | KHÔNG SỬA            | —          | Giữ nguyên, KHÔNG sửa                                                   |
| `bot/handlers/_helpers.py`             | 🎮 B (đọc only)      | —          | Chỉ đọc, KHÔNG sửa                                                      |

### Merge Strategy

- Mỗi stream KHÔNG commit riêng — gộp commit ở bước Finalize
- Nếu 2 streams cùng cần sửa 1 file → stream chạy SAU phải đọc lại file trước khi sửa
- Sync point: sau mỗi wave hoàn thành → verify trước khi bắt đầu wave tiếp
- **Mini App**: Build output `miniapp/dist/` KHÔNG commit vào git → Vercel tự build

---

## Progress Summary

| Stream              | Total  | Done  | Remaining | %      |
| ------------------- | ------ | ----- | --------- | ------ |
| 🏆 A (Services)     | 3      | 3     | 0         | 100%   |
| 🎮 B (Bot)          | 6      | 6     | 0         | 100%   |
| ⚛️ C (Mini App)      | 4 (6-2) | 4   | 0         | 100%   |
| 🔌 D (API)          | 4      | 4     | 0         | 100%   |
| 🧪 E (Testing)      | 3      | 3     | 0         | 100%   |
| **All**             | **20** | **20** | **0**    | **100%** |

---

## Execution Playbook

### Wave 1 — Gamification Services (Sequential ⛓️)

> Stream 🏆 A phải chạy TRƯỚC vì tạo gamification + mood services mà tất cả streams sau depend on.

**Streams**: 🏆 A — Gamification Services
**Chạy**: Tuần tự, 1 chat

#### Prompt — Stream 🏆 A:

```
Triển khai Stream 🏆 A (Gamification Services) trong @TASK_BOARD.md
Đọc section "Context: Codebase Hiện Tại" để hiểu foundation.
Đọc "Conflict Prevention Rules" → chỉ sửa files trong scope.
Đọc docs/GAMIFICATION_DESIGN.md để hiểu hệ thống điểm chi tiết.
Làm từ task P0 trước (A1 → A2 → A3).
```

**✅ Sau khi Wave 1 xong**:

1. Kiểm tra TASK_BOARD.md → confirm tất cả tasks Wave 1 = ✅
2. Verify: `python3 -m py_compile services/gamification_service.py services/mood_service.py services/checkin_service.py`
3. Bắt đầu Wave 2

---

### Wave 2 — Bot + Mini App + API (Parallel 🔀)

> Các streams này KHÔNG depend nhau → chạy SONG SONG trong chat riêng.

**Streams**: 🎮 B (Bot) + ⚛️ C (Mini App) + 🔌 D (API)
**Chạy**: Mỗi stream 1 chat riêng, chạy cùng lúc

#### Prompt — Stream 🎮 B (Chat 1):

```
Triển khai Stream 🎮 B (Gamification Bot Handlers) trong @TASK_BOARD.md
Stream 🏆 A (Gamification Services) đã hoàn thành (Wave 1). Đọc section "Context" + code mới.
Đọc "Conflict Prevention Rules" → chỉ sửa files trong scope.
Đọc services/gamification_service.py và services/mood_service.py để hiểu API.
Đọc docs/GAMIFICATION_DESIGN.md cho format messages, UX copy.
⚠️ Callback data prefix: dùng "mood_" cho mood buttons, "gami_" cho gamification buttons.
Làm từ task P0 trước (B1 → B2 → B3 → B6), sau đó P1 (B4), cuối cùng P2 (B5).
```

#### Prompt — Stream ⚛️ C (Chat 2):

```
Triển khai Stream ⚛️ C (Mini App) trong @TASK_BOARD.md
Stream 🏆 A đã hoàn thành (Wave 1). Đọc section "Context" + code mới.
Đọc "Conflict Prevention Rules" → chỉ sửa files trong scope.
⚠️ Mini App auth: dùng Telegram WebApp.initData → gửi lên API → server validate HMAC-SHA256.
⚠️ Deploy: Vercel tự build miniapp, cần thêm vercel.json rewrite rules.
Làm task C1 → C2 → C3 → C6 (P0). C4, C5 dời sang Phase 5.
```

#### Prompt — Stream 🔌 D (Chat 3):

```
Triển khai Stream 🔌 D (Mini App API) trong @TASK_BOARD.md
Stream 🏆 A đã hoàn thành (Wave 1). Đọc section "Context" + code mới.
Đọc "Conflict Prevention Rules" → chỉ sửa files trong scope.
Đọc services/gamification_service.py để hiểu stats API.
⚠️ Auth: validate Telegram initData bằng HMAC-SHA256 (dùng TELEGRAM_BOT_TOKEN).
⚠️ Vercel serverless pattern: class handler(BaseHTTPRequestHandler).
Làm task D1 → D2 → D3 (P0), sau đó D4 (P1).
```

**✅ Sau khi Wave 2 xong** (cả 3 chat đều hoàn thành):

1. Confirm TASK_BOARD.md → tất cả tasks Wave 2 = ✅
2. Verify: `python3 -m py_compile bot/handlers/gamification.py bot/handlers/mood.py bot/app.py api/me.py api/checkins.py api/leaderboard.py services/auth_service.py`
3. Verify miniapp: `npm run build --prefix miniapp`
4. Bắt đầu Wave 3

---

### Wave 3 — Testing & Launch (Sequential ⛓️)

> Stream 🧪 E cần tất cả code sẵn sàng.

**Streams**: 🧪 E — Testing & Launch
**Chạy**: Tuần tự, 1 chat

#### Prompt — Stream 🧪 E:

```
Triển khai Stream 🧪 E (Testing & Launch) trong @TASK_BOARD.md
Tất cả streams Wave 1 + Wave 2 đã hoàn thành. Đọc section "Context" + code mới.
Task E1: tạo weekly cron endpoint + update GitHub Actions schedule.
Task E2: chạy test checklist theo KNOWN_ISSUES.md §📋 + gamification flow.
Task E3: fix bugs phát hiện.
```

**✅ Sau khi Wave 3 xong**:

1. Confirm TASK_BOARD.md → tất cả tasks = ✅
2. Mở chat mới, chạy Verify & Finalize

---

### Nối tiếp stream (nếu 1 chat bị ngắt giữa chừng):

```
Tiếp tục Stream [X] trong @TASK_BOARD.md — các task [X1, X2] đã xong (✅), tiếp từ [X3].
```

---

### Sau khi TẤT CẢ waves xong — Verify & Finalize:

```
Tất cả streams Phase 4 đã xong. Chạy bước 6-7 của /parallel-phase:
- Verify build (py_compile tất cả files mới/sửa)
- npm run build --prefix miniapp
- Confirm TASK_BOARD.md 100%
- Chạy /code-review trên toàn bộ thay đổi phase
- Finalize: gộp changelog, update PROJECT_CONTEXT.md + DEV_ROADMAP.md, commit
```

---

**Status icons:** 📋 TODO → 🔄 IN PROGRESS → ✅ DONE → ⏸️ BLOCKED

**Priority:** P0 (must have) → P1 (should have) → P2 (nice to have)
