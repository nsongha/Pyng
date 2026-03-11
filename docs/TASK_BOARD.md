# Phase 3 Task Board — Admin & Report (v0.3.0)

> 🎯 Mục tiêu: Admin có đủ công cụ quản lý, xin nghỉ phép hoạt động, báo cáo tự động chạy đúng giờ
> Version target: v0.3.0

## Thuật ngữ

- **Stream**: Nhóm tasks theo domain/concern — mỗi stream chạy trong 1 conversation riêng
- **Wave**: Đợt chạy, gộp 1+ streams cùng execution order (sequential trước, parallel sau)

## Parallel Execution Strategy

Phase này có **18 tasks** chia **4 streams**, **3 waves**:

| Stream                     | Domain                  | Scope                                              | Wave |
| -------------------------- | ----------------------- | -------------------------------------------------- | ---- |
| 🛠️ **Services Foundation** | Services + Config       | `services/`, `config/`, `requirements.txt`         | 1    |
| 👑 **Admin Panel**         | Bot Handlers            | `bot/handlers/`, `bot/app.py`                      | 2    |
| 📋 **Leave Management**    | Bot Handlers + Services | `bot/handlers/`, `services/`                       | 2    |
| 📊 **Report System**       | API + Cron + Bot        | `api/cron/`, `bot/handlers/`, `.github/workflows/` | 3    |

**Execution order**:

1. Wave 1: 🛠️ Services Foundation — tạo services mới (leave, report) + config
2. Wave 2: 👑 Admin Panel + 📋 Leave Management — song song (handler khác nhau)
3. Wave 3: 📊 Report System — phụ thuộc leave_service + checkin_service từ Wave 1

> **Lý do 3 waves**: Report cần aggregate data từ cả checkins + leaves → phải đợi leave_service sẵn sàng. Admin Panel và Leave Management sửa handlers khác nhau → song song an toàn.

---

## Context: Codebase Hiện Tại

### Tech Stack

- **Backend**: Python 3.11+ / python-telegram-bot v21.5 (async webhook)
- **Database**: Supabase PostgreSQL (PostgREST API qua httpx, KHÔNG dùng SDK)
- **Deploy**: Vercel Serverless (auto-deploy từ GitHub)
- **Scheduler**: GitHub Actions Cron
- **Version hiện tại**: v0.2.0 (Phase 2 hoàn thành)

### Foundation Available

- `db/client.py` — REST wrapper (select, insert, update, delete) qua PostgREST API
- `db/schema.sql` — Tables sẵn: `users`, `offices`, `wifi_whitelist`, `nfc_tokens`, `qr_sessions`, `checkins`, **`leaves`**, `gamification`, `point_transactions`, **`system_config`**
- `services/user_service.py` — `register_user()`, `get_by_telegram_id()`, `activate_user()`, `reject_user()`, `is_admin()`, `get_all_active_users()`
- `services/checkin_service.py` — `create_checkin()`, `has_checked_in_today()`, `get_today_checkin()`, `create_checkout()`, `create_wfh_checkin()`, `_today_range()`, `_current_month_range()`
- `services/office_service.py` — `get_active_office()`
- `services/qr_service.py` — QR session CRUD
- `services/nfc_service.py` — NFC token CRUD
- `services/cron_helpers.py` — `verify_cron_secret()`, `send_telegram_message()`, `json_response()`
- `bot/handlers/_helpers.py` — `get_active_user_or_none()`, `get_ontime_status()`, `format_current_time()`
- `bot/handlers/admin.py` — 730 lines, đã có: approval, GPS settings, WiFi whitelist, QR config, NFC management, manual approval
- `bot/handlers/checkin.py` — Re-export module, `get_checkin_handlers()`
- `bot/app.py` — Application factory, đăng ký handlers
- `config/settings.py` — Tất cả env vars (ADMIN_TELEGRAM_IDS, ADMIN_GROUP_ID, WORK_START, WORK_END, LATE_BUDGET_MINUTES, etc.)
- `config/timezone.py` — `get_tz()` singleton
- `requirements.txt` — `openpyxl==3.1.2` commented, chờ uncomment

### DB Schema sẵn có (quan trọng cho Phase 3)

```sql
-- Leaves (sẵn, chưa có service)
CREATE TABLE leaves (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    leave_type VARCHAR(30) NOT NULL,        -- 'annual' | 'compensatory' | 'unpaid' | 'sick'
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    days_count DECIMAL(4, 1),
    reason TEXT,
    status VARCHAR(20) DEFAULT 'pending',   -- 'pending' | 'approved' | 'rejected'
    approved_by INT REFERENCES users(id),
    requested_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP
);

-- System Config (sẵn, chưa có service)
CREATE TABLE system_config (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    updated_by BIGINT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Users (đã có, chú ý annual_leave_days = 12)
-- Users.annual_leave_days INT DEFAULT 12
-- Users.role: 'employee' | 'manager' | 'admin'
-- Users.department VARCHAR(100)
-- Users.is_active BOOLEAN
```

### API Endpoints Available

| Method | Path                   | Mô tả                         |
| ------ | ---------------------- | ----------------------------- |
| POST   | `/api/webhook`         | Nhận Telegram webhook updates |
| POST   | `/api/cron/morning`    | Nhắc check-in 08:30           |
| POST   | `/api/cron/evening`    | Nhắc check-out 17:45          |
| POST   | `/api/cron/qr_refresh` | Refresh QR mỗi 5 phút         |

### Patterns cần tuân theo

1. **Handler pattern**: Mỗi handler file export hàm `get_xxx_handler()` hoặc `get_xxx_handlers()`
2. **Service pattern**: Business logic trong `services/`, KHÔNG trong handler
3. **DB pattern**: Dùng `db.client` (select/insert/update/delete), KHÔNG import httpx trực tiếp
4. **Admin check**: Dùng `ADMIN_TELEGRAM_IDS` hoặc kiểm tra `user["role"] == "admin"`
5. **Cron pattern**: Vercel serverless `class handler(BaseHTTPRequestHandler)`, `do_POST` verify CRON_SECRET, `do_GET` health check
6. **Cron trigger**: GitHub Actions gọi POST với `Authorization: Bearer CRON_SECRET`

---

## Stream 🛠️ A — Services Foundation

**Owner**: Services + Config
**Scope**: `services/leave_service.py`, `services/report_service.py`, `services/config_service.py`, `config/settings.py`, `requirements.txt`

| #   | Task                                  | Status | Priority | Dependencies | Files affected                     |
| --- | ------------------------------------- | ------ | -------- | ------------ | ---------------------------------- |
| A1  | Uncomment openpyxl dependency         | ✅     | P0       | —            | `requirements.txt`                 |
| A2  | Config Service (system_config CRUD)   | ✅     | P0       | —            | `services/config_service.py` [NEW] |
| A3  | Leave Service (CRUD + business logic) | ✅     | P0       | —            | `services/leave_service.py` [NEW]  |
| A4  | Report Service (daily/weekly/monthly) | ✅     | P0       | A1, A3       | `services/report_service.py` [NEW] |
| A5  | Mở rộng User Service (CRUD nhân viên) | ✅     | P1       | —            | `services/user_service.py`         |

**Acceptance Criteria:**

- A1: `openpyxl==3.1.2` uncommented trong requirements.txt. Verify `pip install -r requirements.txt` pass
- A2: `get_config(key)` lấy value từ `system_config`. `set_config(key, value, updated_by)` upsert config. `get_all_configs()` lấy tất cả. Keys dự kiến: `work_start`, `work_end`, `late_budget_minutes`, `checkin_methods_enabled` (JSON array)
- A3: `create_leave_request(user_id, leave_type, start_date, end_date, reason)` tạo đơn pending, tính days_count tự động. `approve_leave(leave_id, approved_by_id)` approve + trừ `annual_leave_days` nếu type='annual'. `reject_leave(leave_id, approved_by_id)` reject. `get_pending_leaves()` danh sách chờ duyệt. `get_user_leaves(user_id, year)` lịch sử nghỉ. `get_remaining_leave_days(user_id)` tính số ngày phép còn lại (annual_leave_days - used)
- A4: `get_daily_report_data(date)` trả về dict {present, absent, wfh, late, on_leave} users. `get_weekly_report_data(start_date, end_date)` aggregate tuần. `generate_monthly_excel(month, year)` tạo Excel file bytes (openpyxl). `generate_daily_text_report(date)` trả về formatted text string cho Telegram
- A5: `get_all_users()` (kể cả inactive). `update_user(telegram_id, data_dict)` cập nhật role/department/is_active. `deactivate_user(telegram_id)` set is_active=False. `get_users_by_role(role)` lọc theo role

---

## Stream 👑 B — Admin Panel

**Owner**: Bot Handlers
**Scope**: `bot/handlers/admin.py`, `bot/handlers/admin_panel.py`, `bot/app.py`

| #   | Task                                  | Status | Priority | Dependencies | Files affected                      |
| --- | ------------------------------------- | ------ | -------- | ------------ | ----------------------------------- |
| B1  | Admin Panel menu chính (/admin)       | ✅     | P0       | A2, A5       | `bot/handlers/admin_panel.py` [NEW] |
| B2  | Quản lý nhân viên (list, edit, deact) | ✅     | P0       | A5, B1       | `bot/handlers/admin_panel.py`       |
| B3  | Cài đặt hệ thống (giờ làm, toggle)    | ✅     | P1       | A2, B1       | `bot/handlers/admin_panel.py`       |
| B4  | Xem lịch sử check-in cá nhân          | ✅     | P1       | B1           | `bot/handlers/admin_panel.py`       |
| B5  | Register admin panel handlers         | ✅     | P0       | B1-B4        | `bot/app.py`                        |

**Acceptance Criteria:**

- B1: `/admin` command → inline keyboard menu: 👥 Quản lý nhân viên, ⚙️ Cài đặt hệ thống, 📊 Báo cáo, ✅ Duyệt thủ công (redirect), 🏢 Cài đặt văn phòng (redirect to existing GPS/WiFi/QR/NFC). Menu navigation bằng callback_data, back button quay về menu chính
- B2: Danh sách nhân viên (tên, role, status). Chọn nhân viên → xem chi tiết (tên, email, role, department, ngày đăng ký). Sửa role (employee/manager/admin). Vô hiệu hóa tài khoản (confirm trước khi deactivate)
- B3: Xem/sửa giờ làm việc (WORK_START, WORK_END). Xem/sửa quỹ muộn (LATE_BUDGET_MINUTES). Toggle bật/tắt từng phương thức check-in (GPS, WiFi, QR, NFC, Manual). Lưu vào `system_config` table
- B4: Admin chọn nhân viên → xem 30 ngày check-in gần nhất (ngày, giờ in, giờ out, method, ontime/late)
- B5: Admin panel handlers đăng ký trong `create_bot()`, KHÔNG conflict với admin handlers cũ (GPS, WiFi, QR, NFC, approval)

> ⚠️ **admin.py đã 730 lines** → tạo file MỚI `admin_panel.py` thay vì thêm vào admin.py. Giữ admin.py cho approval + office settings flows hiện tại

---

## Stream 📋 C — Leave Management

**Owner**: Bot Handlers + Services
**Scope**: `bot/handlers/leave.py`, `bot/app.py`

| #   | Task                                  | Status | Priority | Dependencies | Files affected                |
| --- | ------------------------------------- | ------ | -------- | ------------ | ----------------------------- |
| C1  | Leave request flow (/leave, /xinnghỉ) | ✅     | P0       | A3           | `bot/handlers/leave.py` [NEW] |
| C2  | Manager/Admin approve/reject leave    | ✅     | P0       | A3, C1       | `bot/handlers/leave.py`       |
| C3  | Xem số ngày phép còn lại (/phep)      | ✅     | P1       | A3           | `bot/handlers/leave.py`       |
| C4  | Register leave handlers               | ✅     | P0       | C1-C3        | `bot/app.py`                  |

**Acceptance Criteria:**

- C1: `/leave` hoặc `/xinnghỉ` → ConversationHandler: chọn loại nghỉ (📅 Nghỉ phép năm, 💊 Nghỉ ốm, 🔄 Nghỉ bù, 🚫 Không lương) → nhập ngày bắt đầu (DD/MM/YYYY) → nhập ngày kết thúc → nhập lý do (optional) → xác nhận → gửi. Notification gửi đến admin group. Validate: start_date trong tương lai, end_date >= start_date
- C2: Admin nhận notification với thông tin đơn xin nghỉ. Inline buttons "✅ Duyệt" / "❌ Từ chối". Duyệt → approve_leave (trừ ngày phép nếu annual) → notify user. Từ chối → reject_leave → notify user kèm lý do
- C3: `/phep` → hiển thị: Tổng ngày phép năm, Đã dùng, Còn lại, Danh sách nghỉ gần nhất
- C4: Leave handlers đăng ký trong `create_bot()`

---

## Stream 📊 D — Report System

**Owner**: API + Cron + Bot
**Scope**: `api/cron/daily_report.py`, `bot/handlers/report.py`, `.github/workflows/cron-reminders.yml`, `bot/app.py`

| #   | Task                                     | Status | Priority | Dependencies | Files affected                                       |
| --- | ---------------------------------------- | ------ | -------- | ------------ | ---------------------------------------------------- |
| D1  | Daily report cron endpoint               | ✅     | P0       | A4           | `api/cron/daily_report.py` [NEW]                     |
| D2  | Report bot commands (/report)            | ✅     | P0       | A4           | `bot/handlers/report.py` [NEW]                       |
| D3  | Weekly/Monthly Excel export              | ✅     | P1       | A4, A1       | `bot/handlers/report.py`                             |
| D4  | Register report handlers + cron schedule | ✅     | P0       | D1-D3        | `bot/app.py`, `.github/workflows/cron-reminders.yml` |

**Acceptance Criteria:**

- D1: `POST /api/cron/daily_report` gửi báo cáo text hàng ngày vào admin group (9:15 AM). Format: ✅ Có mặt (N), 🏠 WFH (N), ❌ Vắng (N), ⏰ Muộn (N), 📋 Nghỉ phép (N). Danh sách chi tiết theo từng nhóm
- D2: `/report today` → báo cáo text nhanh hôm nay (ai có mặt, vắng, WFH, nghỉ). `/report week` → summary tuần này (text). `/report month` → summary tháng (text + gửi Excel file). Admin-only commands
- D3: Excel file gồm: Sheet 1 "Tổng hợp" (tên, số ngày đi, muộn, WFH, nghỉ phép), Sheet 2 "Chi tiết" (từng ngày, giờ in/out, method, status). Gửi qua `bot.send_document()` trực tiếp trong Telegram
- D4: Report handlers đăng ký trong `create_bot()`. GitHub Actions cron thêm schedule 9:15 AM UTC+7 = 02:15 UTC

---

## Cross-Stream Dependencies

### Dependency Map

| Task | Depends on | Type         | Notes                                          |
| ---- | ---------- | ------------ | ---------------------------------------------- |
| A4   | A1, A3     | in-stream    | Report service cần openpyxl + leave data       |
| B1   | A2, A5     | cross-stream | Admin panel cần config_service + user CRUD     |
| B2   | A5, B1     | cross-stream | Employee mgmt cần user CRUD từ Wave 1          |
| B3   | A2, B1     | cross-stream | System settings cần config_service từ Wave 1   |
| C1   | A3         | cross-stream | Leave flow cần leave_service từ Wave 1         |
| C2   | A3, C1     | cross-stream | Approval cần leave_service + notification flow |
| D1   | A4         | cross-stream | Daily cron cần report_service từ Wave 1        |
| D2   | A4         | cross-stream | Report commands cần report_service từ Wave 1   |
| D3   | A4, A1     | cross-stream | Excel export cần openpyxl + report_service     |

### Execution Order

1. **Wave 1** (Sequential ⛓️): 🛠️ Stream A — Services Foundation (tạo tất cả services mới)
2. **Wave 2** (Parallel 🔀): 👑 Stream B (Admin Panel) + 📋 Stream C (Leave Management) — independent handlers
3. **Wave 3** (Sequential ⛓️): 📊 Stream D (Report System) — cần A4 + cron schedule

---

## Conflict Prevention Rules

### Shared Files

| File                                   | Streams dùng     | Tasks      | Rule                                                                    |
| -------------------------------------- | ---------------- | ---------- | ----------------------------------------------------------------------- |
| `bot/app.py`                           | 👑 B, 📋 C, 📊 D | B5, C4, D4 | Stream B sửa TRƯỚC (Wave 2). Stream C đọc lại rồi append. Stream D cuối |
| `bot/handlers/admin.py`                | KHÔNG SỬA        | —          | Giữ nguyên 730 lines hiện tại. Admin panel mới → `admin_panel.py`       |
| `requirements.txt`                     | 🛠️ A             | A1         | Chỉ Stream A sửa ở Wave 1                                               |
| `config/settings.py`                   | 🛠️ A             | —          | Chỉ đọc, KHÔNG sửa (system_config thay thế)                             |
| `.github/workflows/cron-reminders.yml` | 📊 D             | D4         | Chỉ Stream D sửa ở Wave 3                                               |
| `services/user_service.py`             | 🛠️ A             | A5         | Chỉ Stream A sửa ở Wave 1 (thêm functions mới)                          |

### Merge Strategy

- Mỗi stream KHÔNG commit riêng — gộp commit ở bước Finalize
- Nếu 2 streams cùng cần sửa 1 file → stream chạy SAU phải đọc lại file trước khi sửa
- Sync point: sau mỗi wave hoàn thành → verify trước khi bắt đầu wave tiếp
- **`bot/app.py` strategy**: Wave 2 có 2 streams cùng sửa → Stream B sửa trước (import admin_panel + register), Stream C đọc lại rồi thêm leave imports

---

## Progress Summary

| Stream          | Total  | Done   | Remaining | %       |
| --------------- | ------ | ------ | --------- | ------- |
| 🛠️ A (Services) | 5      | 5      | 0         | 100%    |
| 👑 B (Admin)    | 5      | 5      | 0         | 100%    |
| 📋 C (Leave)    | 4      | 4      | 0         | 100%    |
| 📊 D (Report)   | 4      | 4      | 0         | 100%    |
| **All**         | **18** | **18** | **0**     | **100%** |

---

## Execution Playbook

### Wave 1 — Services Foundation (Sequential ⛓️)

> Stream 🛠️ A phải chạy TRƯỚC vì tạo services mà các streams khác depend on.

**Streams**: 🛠️ A — Services Foundation
**Chạy**: Tuần tự, 1 chat

#### Prompt — Stream 🛠️ A:

```
Triển khai Stream 🛠️ A (Services Foundation) trong @TASK_BOARD.md
Đọc section "Context: Codebase Hiện Tại" để hiểu foundation.
Đọc "Conflict Prevention Rules" → chỉ sửa files trong scope.
Làm từ task P0 trước (A1 → A2 → A3 → A4), sau đó P1 (A5).
```

**✅ Sau khi Wave 1 xong**:

1. Kiểm tra TASK_BOARD.md → confirm tất cả tasks Wave 1 = ✅
2. Verify: `python3 -m py_compile services/leave_service.py services/report_service.py services/config_service.py services/user_service.py`
3. Bắt đầu Wave 2

---

### Wave 2 — Admin Panel + Leave (Parallel 🔀)

> Các streams này KHÔNG depend nhau → chạy SONG SONG trong chat riêng.

**Streams**: 👑 B (Admin Panel) + 📋 C (Leave Management)
**Chạy**: Mỗi stream 1 chat riêng, chạy cùng lúc

#### Prompt — Stream 👑 B (Chat 1):

```
Triển khai Stream 👑 B (Admin Panel) trong @TASK_BOARD.md
Stream 🛠️ A (Services Foundation) đã hoàn thành (Wave 1). Đọc section "Context" + code mới.
Đọc "Conflict Prevention Rules" → chỉ sửa files trong scope.
Đọc services mới: services/config_service.py, services/user_service.py để hiểu API.
⚠️ Tạo file MỚI bot/handlers/admin_panel.py — KHÔNG sửa admin.py hiện tại.
Làm từ task P0 trước (B1 → B2 → B5), sau đó P1 (B3 → B4).
```

#### Prompt — Stream 📋 C (Chat 2):

```
Triển khai Stream 📋 C (Leave Management) trong @TASK_BOARD.md
Stream 🛠️ A (Services Foundation) đã hoàn thành (Wave 1). Đọc section "Context" + code mới.
Đọc "Conflict Prevention Rules" → chỉ sửa files trong scope.
Đọc services/leave_service.py để hiểu API.
⚠️ Đọc lại bot/app.py vì Stream B có thể đã sửa (nếu B xong trước).
Làm task C1 → C2 → C3 → C4.
```

**✅ Sau khi Wave 2 xong** (cả 2 chat đều hoàn thành):

1. Confirm TASK_BOARD.md → tất cả tasks Wave 2 = ✅
2. Verify: `python3 -m py_compile bot/handlers/admin_panel.py bot/handlers/leave.py bot/app.py`
3. Bắt đầu Wave 3

---

### Wave 3 — Report System (Sequential ⛓️)

> Stream 📊 D cần report_service + tất cả data sources sẵn sàng.

**Streams**: 📊 D — Report System
**Chạy**: Tuần tự, 1 chat

#### Prompt — Stream 📊 D:

```
Triển khai Stream 📊 D (Report System) trong @TASK_BOARD.md
Stream 🛠️ A (Wave 1) và Streams 👑 B + 📋 C (Wave 2) đã hoàn thành.
Đọc section "Context" + code mới trong services/report_service.py.
Đọc "Conflict Prevention Rules" → chỉ sửa files trong scope.
⚠️ Đọc lại bot/app.py vì Wave 2 đã sửa.
Làm từ task P0 trước (D1 → D2 → D4), sau đó P1 (D3).
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
Tất cả streams Phase 3 đã xong. Chạy bước 6-7 của /parallel-phase:
- Verify build (py_compile tất cả files mới/sửa)
- Confirm TASK_BOARD.md 100%
- Chạy /code-review trên toàn bộ thay đổi phase
- Finalize: gộp changelog, update PROJECT_CONTEXT.md + DEV_ROADMAP.md, commit
```

---

**Status icons:** 📋 TODO → 🔄 IN PROGRESS → ✅ DONE → ⏸️ BLOCKED

**Priority:** P0 (must have) → P1 (should have) → P2 (nice to have)
