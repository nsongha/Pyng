# Phase 1 — MVP Core Task Board

## Parallel Execution Strategy

**Mục tiêu**: Nhân viên có thể đăng ký qua bot và check-in bằng GPS + WiFi. Scheduler nhắc nhở hoạt động.

**Streams**: 3 streams song song, tối thiểu file overlap:

| Stream                 | Domain                                                           | Scope                                                |
| ---------------------- | ---------------------------------------------------------------- | ---------------------------------------------------- |
| 🛢️ Database & Services | `services/`, `db/`                                               | DB client, user/checkin services                     |
| 🤖 Bot Handlers        | `bot/handlers/`, `bot/validators/`, `bot/app.py`                 | Registration, checkin, checkout, WFH, admin handlers |
| ⏰ Infra & Cron        | `api/cron/`, `.github/workflows/`, `requirements.txt`, `config/` | Cron endpoints, GitHub Actions, dependencies         |

**Execution order**: 🛢️ Database → 🤖 Bot (depends on services) → ⏰ Infra (independent, chạy song song với Bot)

---

## Context: Codebase Hiện Tại

### Foundation đã có (Phase 0 ✅)

- **`config/settings.py`** — Env vars đầy đủ (Telegram, DB, Office, Policy, WiFi, Admin)
- **`bot/app.py`** — Application factory, chỉ có `/start` handler
- **`bot/handlers/start.py`** — Hello world response, chưa có registration flow
- **`api/webhook.py`** — Vercel serverless handler, xử lý POST/GET
- **`db/schema.sql`** — 10 tables đã tạo trên Supabase (users, offices, checkins, wifi_whitelist, etc.)
- **`vercel.json`** — Routes + security headers
- **`requirements.txt`** — Chỉ active: `python-telegram-bot`, `python-dotenv`, `httpx`, `pydantic`. Phần lớn Phase 1 deps đang commented out

### Chưa có

- `services/` — trống (chỉ `__init__.py`)
- `bot/validators/` — trống (chỉ `__init__.py`)
- `api/cron/` — trống
- DB client/connection module chưa có
- Không có tests

---

## Stream 🛢️ Database & Services

**Owner**: Backend Core
**Scope**: `services/`, `db/`, `requirements.txt`

| #   | Task                                                                                                | Status | Priority | Dependencies | Files affected                     |
| --- | --------------------------------------------------------------------------------------------------- | ------ | -------- | ------------ | ---------------------------------- |
| A1  | Uncomment & cài đặt Phase 1 dependencies (`supabase`, `geopy`, `pydantic`)                          | ✅     | P0       | -            | `requirements.txt`                 |
| A2  | Tạo Supabase DB client module (connection, query helpers)                                           | ✅     | P0       | A1           | `db/client.py`                     |
| A3  | Tạo `services/user_service.py` — CRUD users (register, get_by_telegram_id, update status, is_admin) | ✅     | P0       | A2           | `services/user_service.py`         |
| A4  | Tạo `services/checkin_service.py` — create checkin, get today's checkin, check duplicate, checkout  | ✅     | P0       | A2           | `services/checkin_service.py`      |
| A5  | Tạo `bot/validators/gps_validator.py` — geofence check, distance calc, spoofing detection           | ✅     | P0       | A1           | `bot/validators/gps_validator.py`  |
| A6  | Tạo `bot/validators/wifi_validator.py` — SSID whitelist check                                       | ✅     | P1       | A2           | `bot/validators/wifi_validator.py` |
| A7  | Tạo `services/office_service.py` — CRUD offices, get active office, update geofence                 | ✅     | P1       | A2           | `services/office_service.py`       |

**Acceptance Criteria:**

- A2: `db/client.py` có thể query Supabase thành công (test insert/select)
- A3: Register user, check exists, get by telegram_id hoạt động
- A4: Tạo record checkin/checkout, lấy checkin hôm nay, chặn duplicate
- A5: Tính distance chính xác, phát hiện spoofing (speed > 500km/h)
- A6: Match SSID với whitelist từ DB
- A7: Get office coordinates, update radius

---

## Stream 🤖 Bot Handlers

**Owner**: Bot Layer
**Scope**: `bot/handlers/`, `bot/app.py`

| #   | Task                                                                                           | Status | Priority | Dependencies | Files affected                          |
| --- | ---------------------------------------------------------------------------------------------- | ------ | -------- | ------------ | --------------------------------------- |
| B1  | Refactor `/start` → registration flow (nhập tên, email, chờ admin duyệt) + ConversationHandler | ✅     | P0       | A3 ✅        | `bot/handlers/start.py`, `bot/app.py`   |
| B2  | Admin approval flow — notification + inline buttons (Duyệt / Từ chối)                          | ✅     | P0       | A3 ✅        | `bot/handlers/admin.py`, `bot/app.py`   |
| B3  | GPS check-in handler — nhận location, validate, lưu DB, response đẹp                           | ✅     | P0       | A4, A5 ✅    | `bot/handlers/checkin.py`, `bot/app.py` |
| B4  | WiFi check-in handler — nhập SSID, validate, lưu DB                                            | ✅     | P0       | A4, A6 ✅    | `bot/handlers/checkin.py`               |
| B5  | Check-out handler — flow checkout, tính working hours                                          | ✅     | P1       | A4 ✅        | `bot/handlers/checkin.py`               |
| B6  | WFH flow — đăng ký WFH, check limit 2 lần/tháng                                                | ✅     | P1       | A4 ✅        | `bot/handlers/checkin.py`               |
| B7  | Admin GPS settings — set geofence radius qua bot                                               | ✅     | P2       | A7 ✅        | `bot/handlers/admin.py`                 |
| B8  | Admin WiFi whitelist management — thêm/xóa SSID                                                | ✅     | P2       | A6 ✅        | `bot/handlers/admin.py`                 |

**Acceptance Criteria:**

- B1: User mới → nhập tên → nhập email → lưu DB pending → admin nhận notification
- B2: Admin bấm Duyệt → user nhận thông báo "Đã duyệt", status = active
- B3: Share location → validate geofence → success/fail response đầy đủ (streak, điểm, thời gian)
- B4: Nhập WiFi SSID → match whitelist → check-in thành công
- B5: `/checkout` → tính working hours → lưu DB → response đẹp
- B6: WFH → check 2 lần/tháng → lưu → confirm
- B7: Admin thay đổi radius → cập nhật office trong DB
- B8: Admin thêm/xóa WiFi SSID → cập nhật whitelist

---

## Stream ⏰ Infra & Cron

**Owner**: DevOps / Scheduler
**Scope**: `api/cron/`, `.github/workflows/`

| #   | Task                                                                                   | Status | Priority | Dependencies | Files affected                         |
| --- | -------------------------------------------------------------------------------------- | ------ | -------- | ------------ | -------------------------------------- |
| C1  | Tạo cron morning reminder endpoint (`/api/cron/morning.py`) — gửi nhắc check-in 8:30   | 📋     | P0       | A3           | `api/cron/morning.py`                  |
| C2  | Tạo cron evening reminder endpoint (`/api/cron/evening.py`) — gửi nhắc check-out 17:45 | 📋     | P1       | A3, A4       | `api/cron/evening.py`                  |
| C3  | Setup GitHub Actions Cron workflows (morning 8:30, evening 17:45)                      | 📋     | P1       | C1, C2       | `.github/workflows/cron-reminders.yml` |

**Acceptance Criteria:**

- C1: Endpoint `/api/cron/morning` → gửi tin nhắn nhắc check-in cho all active users, có xác thực CRON_SECRET
- C2: Endpoint `/api/cron/evening` → gửi nhắc check-out cho users đã check-in nhưng chưa check-out
- C3: GitHub Actions trigger đúng giờ (UTC+7), gọi endpoints thành công

---

## Cross-Stream Dependencies

| Task | Depends on   | Type         | Notes                                             |
| ---- | ------------ | ------------ | ------------------------------------------------- |
| B1   | A3 ✅        | cross-stream | Registration cần user_service                     |
| B2   | A3 ✅        | cross-stream | Admin approval cần user_service                   |
| B3   | A4 ✅, A5 ✅ | cross-stream | GPS checkin cần checkin_service + gps_validator   |
| B4   | A4 ✅, A6 ✅ | cross-stream | WiFi checkin cần checkin_service + wifi_validator |
| B5   | A4 ✅        | cross-stream | Checkout cần checkin_service                      |
| C1   | A3           | cross-stream | Morning cron cần user_service                     |
| C2   | A3, A4       | cross-stream | Evening cron cần user+checkin services            |

**Execution Order khuyến nghị:**

1. 🛢️ Stream A (Database & Services) → chạy **trước**
2. 🤖 Stream B (Bot Handlers) + ⏰ Stream C (Infra) → chạy **song song** sau khi A1-A5 xong

---

## Progress Summary

| Stream                 | Total  | Done   | Remaining | %       |
| ---------------------- | ------ | ------ | --------- | ------- |
| 🛢️ Database & Services | 7      | 7      | 0         | 100%    |
| 🤖 Bot Handlers        | 8      | 8      | 0         | 100%    |
| ⏰ Infra & Cron        | 3      | 0      | 3         | 0%      |
| **TOTAL**              | **18** | **15** | **3**     | **83%** |

---

## Execution Playbook

### Wave 1 — Foundation (Sequential ⛓️)

> Stream 🛢️ phải chạy TRƯỚC vì Stream 🤖 và ⏰ đều depend on services/validators.

**Streams**: 🛢️ Database & Services
**Chạy**: 1 chat duy nhất

#### Prompt — Stream 🛢️ Database & Services:

```
Triển khai Stream 🛢️ Database & Services trong @TASK_BOARD.md
Đọc section "Context: Codebase Hiện Tại" để hiểu foundation.
Làm từ task P0 trước (A1 → A2 → A3 → A4 → A5), sau đó P1 (A6, A7).
```

**✅ Sau khi Wave 1 xong**:

1. Kiểm tra TASK_BOARD.md → confirm A1-A7 = ✅
2. Verify: `python3 -m py_compile db/client.py services/user_service.py services/checkin_service.py bot/validators/gps_validator.py bot/validators/wifi_validator.py services/office_service.py`
3. Bắt đầu Wave 2

---

### Wave 2 — Bot + Infra (Parallel 🔀)

> 🤖 Bot Handlers và ⏰ Infra KHÔNG depend nhau → chạy SONG SONG trong 2 chat riêng.

**Streams**: 🤖 Bot Handlers + ⏰ Infra & Cron
**Chạy**: 2 chat song song

#### Prompt — Stream 🤖 Bot Handlers (Chat 1):

```
Triển khai Stream 🤖 Bot Handlers trong @TASK_BOARD.md
Stream 🛢️ Database & Services đã hoàn thành (Wave 1).
Đọc section "Context" + code mới trong db/client.py, services/, bot/validators/.
Làm từ task P0 trước (B1 → B2 → B3 → B4), sau đó P1 (B5, B6), cuối cùng P2 (B7, B8).
```

#### Prompt — Stream ⏰ Infra & Cron (Chat 2):

```
Triển khai Stream ⏰ Infra & Cron trong @TASK_BOARD.md
Stream 🛢️ Database & Services đã hoàn thành (Wave 1).
Đọc section "Context" + code mới trong db/client.py, services/.
Làm task C1 → C2 → C3.
```

**✅ Sau khi Wave 2 xong** (cả 2 chat đều hoàn thành):

1. Confirm TASK_BOARD.md → 18/18 tasks = ✅
2. Mở chat mới, chạy bước Verify & Review (bên dưới)

---

### Nối tiếp stream (nếu 1 chat bị ngắt giữa chừng):

```
Tiếp tục Stream [🤖/⏰] trong @TASK_BOARD.md — các task [X1, X2] đã xong (✅), tiếp từ [X3].
```

---

### Sau khi TẤT CẢ waves xong — Verify & Finalize:

```
Tất cả streams Phase 1 đã xong. Chạy bước 6-7 của /parallel-phase:
- Verify build (py_compile tất cả files)
- Confirm TASK_BOARD.md 100%
- Chạy /code-review trên toàn bộ thay đổi phase
- Finalize: gộp changelog, update PROJECT_CONTEXT.md + DEV_ROADMAP.md, commit
```
