# Phase 5 Task Board — Enhancement (v0.5.0)

> 🎯 Mục tiêu: Nâng cấp trải nghiệm — chart thống kê, xin nghỉ qua Mini App, overtime tracking, export tùy chọn, fix tech debt
> Version target: v0.5.0

## Thuật ngữ

- **Stream**: Nhóm tasks theo domain/concern — mỗi stream chạy trong 1 conversation riêng
- **Wave**: Đợt chạy, gộp 1+ streams cùng execution order (sequential trước, parallel sau)

## Parallel Execution Strategy

Phase này có **18 tasks** chia **4 streams**, **3 waves**:

| Stream                       | Domain                   | Scope                                                   | Wave |
| ---------------------------- | ------------------------ | ------------------------------------------------------- | ---- |
| 🔧 **Backend Enhancement**  | Services + API + Bot     | `services/`, `api/`, `bot/handlers/`                    | 1    |
| 📊 **Mini App Charts**      | React Frontend           | `miniapp/src/`                                          | 2    |
| 📝 **Mini App Leave Form**  | React + API              | `miniapp/src/`, `api/`                                  | 2    |
| 🧪 **Testing & Polish**     | QA + Docs + Tech Debt    | `docs/`, `api/`, `services/`                            | 3    |

**Execution order**:

1. Wave 1: 🔧 Backend Enhancement — overtime service, report mở rộng, API mới
2. Wave 2: 📊 Mini App Charts + 📝 Mini App Leave Form — song song (khác pages/components)
3. Wave 3: 🧪 Testing & Polish — QC, tech debt fix, docs update

> **Lý do 3 waves**: Charts và Leave Form cần API mở rộng (Wave 1). Hai stream Mini App khác page/component → song song an toàn. Testing cuối cùng.

---

## Context: Codebase Hiện Tại

### Tech Stack

- **Backend**: Python 3.11+ / python-telegram-bot v21.5 (async webhook)
- **Database**: Supabase PostgreSQL (PostgREST API qua httpx, KHÔNG dùng SDK)
- **Deploy**: Vercel Serverless (auto-deploy từ GitHub)
- **Scheduler**: GitHub Actions Cron
- **Frontend**: React 18 + Vite + Tailwind v4 (đã scaffold, có Dashboard page)
- **Version hiện tại**: v0.4.0 (Phase 4 hoàn thành)

### Foundation Available

- `services/report_service.py` — daily/weekly/monthly reports + Excel export. Có sẵn `generate_monthly_excel(month, year)`, `get_daily_report_data()`, `get_weekly_report_data()`. **Chưa có** export theo khoảng ngày tùy chọn
- `services/checkin_service.py` — `create_checkin()`, `get_today_checkin()`, `create_checkout()`, `create_wfh_checkin()`. Lưu `checked_at` timestamp
- `services/leave_service.py` — `create_leave_request()`, `get_user_leaves()`, `approve_leave()`, `reject_leave()`. **Chưa có** API endpoint cho Mini App
- `services/auth_service.py` — `validate_telegram_init_data()`, decorator pattern cho API auth. Chỉ hỗ trợ GET methods
- `services/gamification_service.py` — `get_user_stats()`, `get_leaderboard()`

- `miniapp/src/pages/Dashboard.tsx` — 1 page duy nhất: stats + gamification + history list
- `miniapp/src/lib/api.ts` — `fetchMe()`, `fetchCheckins()`, `fetchLeaderboard()`. **Chưa có** chart data, leave API
- `miniapp/src/types/index.ts` — TypeScript types đầy đủ. **Chưa có** OvertimeRecord, ChartData, LeaveRequest types
- `miniapp/src/App.tsx` — Single page (Dashboard), **chưa có** routing
- `miniapp/src/contexts/TelegramContext.tsx` — WebApp integration, auth, profile fetch

- `api/me.py`, `api/checkins.py`, `api/leaderboard.py` — GET endpoints cho Mini App (auth: `X-Telegram-Init-Data`)
- **Chưa có**: `/api/leave/*`, `/api/report/export`, `/api/checkins/chart` endpoints
- `bot/handlers/report.py` — `/report today|week|month`. **Chưa có** custom date range
- `bot/handlers/admin.py` — Manual approval 1-by-1. **Chưa có** bulk approve

### DB Schema Relevant (đã có sẵn)

```sql
-- Checkins: đã có working hours implicit (checked_at IN/OUT)
CREATE TABLE checkins (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    type VARCHAR(10) NOT NULL,     -- 'in' | 'out'
    method VARCHAR(20) NOT NULL,
    checked_at TIMESTAMP DEFAULT NOW()
);

-- Leaves: đầy đủ cho leave form
CREATE TABLE leaves (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    leave_type VARCHAR(30) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    days_count DECIMAL(4,1),
    reason TEXT,
    status VARCHAR(20) DEFAULT 'pending'
);

-- Gamification: stats cho charts
CREATE TABLE gamification (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) UNIQUE,
    total_points INT DEFAULT 0,
    current_streak INT DEFAULT 0,
    longest_streak INT DEFAULT 0,
    ontime_count INT DEFAULT 0,
    early_count INT DEFAULT 0
);
```

### Patterns cần tuân theo

1. **Handler pattern**: Mỗi handler file export hàm `get_xxx_handler()` hoặc `get_xxx_handlers()`
2. **Service pattern**: Business logic trong `services/`, KHÔNG trong handler
3. **DB pattern**: Dùng `db.client` (select/insert/update/delete), KHÔNG import httpx trực tiếp
4. **API pattern**: Vercel serverless, `class handler(BaseHTTPRequestHandler)`, auth qua `X-Telegram-Init-Data`
5. **Mini App routing**: Chưa có — cần thêm react-router-dom cho multiple pages
6. **Admin check**: `ADMIN_TELEGRAM_IDS` hoặc `user["role"] == "admin"`

---

## Stream 🔧 A — Backend Enhancement

**Owner**: Services + API + Bot
**Scope**: `services/report_service.py`, `services/overtime_service.py`, `api/`, `bot/handlers/report.py`, `bot/handlers/admin.py`

| #   | Task                                        | Status | Priority | Dependencies | Files affected                           |
| --- | ------------------------------------------- | ------ | -------- | ------------ | ---------------------------------------- |
| A1  | Overtime Service (tracking + tính OT)       | ✅     | P0       | —            | `services/overtime_service.py` [NEW]     |
| A2  | Report export theo khoảng ngày tùy chọn    | ✅     | P0       | —            | `services/report_service.py`             |
| A3  | Bot command: /report custom date            | ✅     | P1       | A2           | `bot/handlers/report.py`                 |
| A4  | Bulk approve manual check-in                | ✅     | P1       | —            | `bot/handlers/admin.py`                  |
| A5  | API: GET /api/checkins/chart (chart data)   | ✅     | P0       | —            | `api/checkins/chart.py` [NEW]            |
| A6  | API: POST /api/leave/request                | ✅     | P0       | —            | `api/leave/request.py` [NEW]             |
| A7  | API: GET /api/leave/my                      | ✅     | P0       | —            | `api/leave/my.py` [NEW]                  |
| A8  | API: GET /api/overtime (user OT data)       | ✅     | P1       | A1           | `api/overtime.py` [NEW]                  |

**Acceptance Criteria:**

- A1: Overtime tracking service:
  - `calculate_overtime(user_id, date)` → so sánh checkout time với WORK_END (17:45), trả về minutes OT
  - `get_monthly_overtime(user_id, month, year)` → tổng OT tháng (total_minutes, total_days, sessions list)
  - `get_overtime_report(month, year)` → tổng hợp OT toàn bộ nhân viên
  - OT chỉ tính khi checkout sau WORK_END + 30 phút (avoid false positives từ late checkout)
  - OT cap tại 4 giờ/ngày (tránh quên checkout)
- A2: `generate_custom_range_excel(start_date, end_date)` → Excel report cho khoảng ngày tuỳ chọn. Cùng format với `generate_monthly_excel()` nhưng nhận date range thay vì month/year
- A3: Bot command `/report YYYY-MM-DD YYYY-MM-DD` → gửi Excel cho admin. Validate date format, max 90 ngày range. Chỉ admin dùng được
- A4: Bulk approve: admin reply "duyệt tất cả" hoặc inline button `[✅ Duyệt tất cả pending]` trong `/admin` → approve all pending manual check-ins. Gửi notification cho từng user được approve. Callback data prefix: `bulk_`
- A5: `GET /api/checkins/chart?month=2026-03` (auth required):
  - `daily_hours`: mảng 31 items (1 per day), mỗi item = `{date, hours, is_late, method, mood}`
  - `summary`: `{avg_hours, total_days, ontime_rate, most_used_method}`
  - `trend`: `{prev_month_avg, current_avg, change_percent}` (so sánh với tháng trước)
- A6: `POST /api/leave/request` (auth required):
  - Body: `{leave_type, start_date, end_date, reason}`
  - Validate: dates hợp lệ, không overlap với leave đã có, đủ ngày phép (annual)
  - Tạo leave request qua `leave_service.create_leave_request()`
  - Gửi notification cho admin group qua Telegram Bot API (httpx)
- A7: `GET /api/leave/my?year=2026` (auth required):
  - Trả về `{leaves: LeaveRequest[], balance: {total, used, remaining}}`
  - Sorted by requested_at DESC
- A8: `GET /api/overtime?month=2026-03` (auth required):
  - Trả về `{total_minutes, total_days, sessions: [{date, minutes, checkout_time}]}`

---

## Stream 📊 B — Mini App Charts

**Owner**: React Frontend
**Scope**: `miniapp/src/` (pages, components, lib, types)

| #   | Task                                    | Status | Priority | Dependencies | Files affected                       |
| --- | --------------------------------------- | ------ | -------- | ------------ | ------------------------------------ |
| B1  | React Router setup + bottom navigation  | ✅     | P0       | —            | `miniapp/src/App.tsx`, `package.json` |
| B2  | Chart components (working hours + attendance) | ✅ | P0  | A5           | `miniapp/src/components/charts/` [NEW] |
| B3  | Charts page                             | ✅     | P0       | B1, B2       | `miniapp/src/pages/Charts.tsx` [NEW] |
| B4  | Overtime card + chart                   | ✅     | P1       | A8, B1       | `miniapp/src/components/OvertimeCard.tsx` [NEW] |
| B5  | API client mở rộng (chart + OT)        | ✅     | P0       | A5, A8       | `miniapp/src/lib/api.ts`, `miniapp/src/types/index.ts` |

**Acceptance Criteria:**

- B1: Thêm `react-router-dom`. Bottom navigation bar: 3 tabs [📊 Dashboard] [📈 Thống kê] [📋 Nghỉ phép]. Active tab highlight. Smooth transition giữa pages. Back button Telegram xử lý navigate back
- B2: Chart components:
  - `WorkingHoursChart` — bar chart 30 ngày (mỗi bar = 1 ngày, height = hours). Color: xanh = đúng giờ, đỏ = muộn. Hover/tap show detail tooltip
  - `AttendanceDonut` — donut chart: present %, WFH %, leave %, absent %
  - Dùng thư viện nhẹ: **recharts** hoặc **Chart.js + react-chartjs-2** (recommend recharts vì bundle nhỏ hơn)
  - Responsive, theme-aware (dùng Telegram theme colors)
- B3: Charts page layout:
  - Month selector (prev/next arrows, hiển thị "Tháng 3/2026")
  - WorkingHoursChart (full-width)
  - Stats summary row: avg hours, ontime %, trend
  - AttendanceDonut
  - OvertimeCard (nếu có OT data)
- B4: Overtime card: hiển thị tổng OT tháng (giờ:phút), số sessions. Mini chart trend (simple sparkline)
- B5: Thêm `fetchChartData(initData, month)`, `fetchOvertime(initData, month)` vào api.ts. Thêm types: `ChartDataResponse`, `OvertimeResponse` vào types/index.ts

---

## Stream 📝 C — Mini App Leave Form

**Owner**: React + API
**Scope**: `miniapp/src/` (pages, components, lib, types)

| #   | Task                             | Status | Priority | Dependencies | Files affected                          |
| --- | -------------------------------- | ------ | -------- | ------------ | --------------------------------------- |
| C1  | Leave request form component     | ✅     | P0       | A6           | `miniapp/src/components/LeaveForm.tsx` [NEW] |
| C2  | Leave list + status component    | ✅     | P0       | A7           | `miniapp/src/components/LeaveList.tsx` [NEW] |
| C3  | Leave page (list + form)         | ✅     | P0       | B1, C1, C2   | `miniapp/src/pages/Leave.tsx` [NEW]     |
| C4  | API client mở rộng (leave)       | ✅     | P0       | A6, A7       | `miniapp/src/lib/api.ts`, types         |

**Acceptance Criteria:**

- C1: Leave form:
  - Fields: Loại nghỉ (annual/sick/compensatory/unpaid — dropdown), Từ ngày (date picker), Đến ngày (date picker), Lý do (textarea)
  - Tự tính days_count (end - start + 1, trừ weekend)
  - Validate: từ ngày ≤ đến ngày, lý do bắt buộc cho unpaid/compensatory
  - Hiển thị "Phép còn lại: X ngày" nếu loại = annual
  - Submit → POST /api/leave/request → toast thành công / lỗi
  - Telegram haptic feedback khi submit
- C2: Leave list:
  - Danh sách leave requests sorted by date DESC
  - Badge status: 🟡 Pending, ✅ Approved, ❌ Rejected
  - Pull-to-refresh
  - Empty state khi chưa có leave nào
- C3: Leave page:
  - Tab/toggle: [📋 Danh sách] [➕ Xin nghỉ]
  - Balance card trên cùng: "Phép năm còn X/12 ngày"
  - Danh sách tab hiển thị LeaveList
  - Xin nghỉ tab hiển thị LeaveForm
- C4: Thêm `fetchMyLeaves(initData, year)`, `submitLeaveRequest(initData, data)` vào api.ts. Thêm types: `LeaveRequest`, `LeaveFormData`, `MyLeavesResponse`

---

## Stream 🧪 D — Testing & Polish

**Owner**: QA + Tech Debt + Docs
**Scope**: `api/leaderboard.py`, `services/auth_service.py`, `docs/`

| #   | Task                               | Status | Priority | Dependencies    | Files affected                |
| --- | ---------------------------------- | ------ | -------- | --------------- | ----------------------------- |
| D1  | Fix TD-001: N+1 query leaderboard | ✅     | P1       | —               | `api/leaderboard.py`          |
| D2  | Fix TD-002: CORS restrict          | ✅     | P2       | —               | `services/auth_service.py`    |
| D3  | Test toàn bộ flows (QC Report)     | ✅     | P0       | Tất cả streams  | `docs/QC_REPORT.md`           |
| D4  | Fix bugs từ testing                | ✅     | P0       | D3              | Không phát hiện bug            |

**Acceptance Criteria:**

- D1: N+1 query fix: batch load tất cả user names trong 1 query thay vì per-entry. Pattern: `db.select("users", filters={"id.in": user_ids_string})` → build map → enrich. Tham khảo `bot/handlers/gamification.py` đã làm đúng
- D2: CORS: thay `Access-Control-Allow-Origin: *` bằng `MINI_APP_URL` từ settings. Fallback `*` cho dev. Check `MINI_APP_URL` environment variable
- D3: Chạy full QC: import test tất cả modules mới, code path trace cho overtime, chart API, leave API. Test Mini App build
- D4: Fix tất cả P0/P1 bugs phát hiện

---

## Cross-Stream Dependencies

### Dependency Map

| Task | Depends on | Type         | Notes                                        |
| ---- | ---------- | ------------ | -------------------------------------------- |
| A3   | A2         | in-stream    | Bot custom report cần report_service mở rộng |
| A5   | —          | standalone   | Chart API independent                        |
| A6   | —          | standalone   | Leave API independent (dùng leave_service cũ) |
| A8   | A1         | in-stream    | OT API cần overtime_service                  |
| B2   | A5         | cross-stream | Chart components cần chart API data          |
| B3   | B1, B2     | in-stream    | Charts page cần router + chart components    |
| B4   | A8         | cross-stream | OT card cần overtime API                     |
| B5   | A5, A8     | cross-stream | API client cần biết response format          |
| C1   | A6         | cross-stream | Leave form cần leave API endpoint            |
| C2   | A7         | cross-stream | Leave list cần leave list API                |
| C3   | B1, C1, C2 | cross-stream | Leave page cần router + form + list          |
| C4   | A6, A7     | cross-stream | API client cần leave endpoints               |
| D3   | All        | cross-stream | QC cần tất cả xong                           |

### Execution Order

1. **Wave 1** (Sequential ⛓️): 🔧 Stream A — Backend Enhancement (tạo services + API endpoints)
2. **Wave 2** (Parallel 🔀): 📊 Stream B (Charts) + 📝 Stream C (Leave Form) — independent pages/components
3. **Wave 3** (Sequential ⛓️): 🧪 Stream D — Testing & Polish

---

## Conflict Prevention Rules

### Shared Files

| File                          | Streams dùng   | Tasks  | Rule                                                           |
| ----------------------------- | -------------- | ------ | -------------------------------------------------------------- |
| `miniapp/src/App.tsx`         | 📊 B           | B1     | Chỉ Stream 📊 sửa (thêm router + bottom nav)                  |
| `miniapp/src/lib/api.ts`     | 📊 B + 📝 C    | B5, C4 | Stream 📊 sửa TRƯỚC (B5), Stream 📝 sửa SAU (C4) — đọc lại file |
| `miniapp/src/types/index.ts` | 📊 B + 📝 C    | B5, C4 | Stream 📊 sửa TRƯỚC, Stream 📝 append thêm                     |
| `bot/handlers/report.py`     | 🔧 A           | A3     | Chỉ Stream 🔧 sửa                                              |
| `bot/handlers/admin.py`      | 🔧 A           | A4     | Chỉ Stream 🔧 sửa                                              |
| `services/report_service.py` | 🔧 A           | A2     | Chỉ Stream 🔧 sửa                                              |
| `services/auth_service.py`   | 🧪 D           | D2     | Chỉ Stream 🧪 sửa ở Wave 3                                     |
| `api/leaderboard.py`         | 🧪 D           | D1     | Chỉ Stream 🧪 sửa ở Wave 3                                     |
| `bot/app.py`                 | KHÔNG SỬA       | —      | Giữ nguyên (không có handler mới cần đăng ký)                  |

### File Conflict Resolution: api.ts + types

> ⚠️ `miniapp/src/lib/api.ts` và `miniapp/src/types/index.ts` được sửa bởi CẢ 2 stream B và C.

**Rule**: Stream 📊 B (Wave 2, Chat 1) sửa **TRƯỚC** — thêm chart + overtime functions/types.
Stream 📝 C (Wave 2, Chat 2) **PHẢI đọc lại** file trước khi sửa — append leave functions/types.
Cả 2 stream chỉ **APPEND** (thêm mới), KHÔNG sửa existing code.

### Merge Strategy

- Mỗi stream KHÔNG commit riêng — gộp commit ở bước Finalize
- Nếu 2 streams cùng cần sửa 1 file → stream chạy SAU phải đọc lại file trước khi sửa
- Sync point: sau mỗi wave hoàn thành → verify trước khi bắt đầu wave tiếp
- **Mini App**: Build output `miniapp/dist/` KHÔNG commit vào git → Vercel tự build

---

## Progress Summary

| Stream              | Total  | Done  | Remaining | %    |
| ------------------- | ------ | ----- | --------- | ---- |
| 🔧 A (Backend)      | 8      | 8     | 0         | 100% |
| 📊 B (Charts)       | 5      | 5     | 0         | 100% |
| 📝 C (Leave)        | 4      | 4     | 0         | 100% |
| 🧪 D (Testing)      | 4      | 4     | 0         | 100% |
| **All**             | **21** | **21** | **0**    | **100%** |

---

## QC Test Plan

### Stream 🔧 A — Backend Enhancement

- TC-OT-01: Overtime calculation — checkout 19:00 → OT = 45 phút (17:45 + 30min grace → 18:15, 19:00-18:15=45min)
  → Input: user checkout at 19:00
  → Expected: 45 minutes OT
  → Type: happy

- TC-OT-02: Overtime not triggered — checkout 18:00 (within 30min grace)
  → Input: user checkout at 18:00
  → Expected: 0 minutes OT (within grace period)
  → Type: edge

- TC-OT-03: Overtime cap — checkout 23:30 (quên checkout? → cap 4h)
  → Input: user checkout at 23:30
  → Expected: 240 minutes OT (4h cap)
  → Type: edge

- TC-RPT-01: Custom date range report — 2026-03-01 to 2026-03-10
  → Input: start=2026-03-01, end=2026-03-10
  → Expected: Excel file với chi tiết 10 ngày
  → Type: happy

- TC-RPT-02: Custom range — quá 90 ngày → reject
  → Input: start=2026-01-01, end=2026-12-31
  → Expected: Error "Max range is 90 days"
  → Type: error

- TC-BULK-01: Bulk approve — 3 pending manual check-ins
  → Input: admin click "Duyệt tất cả"
  → Expected: 3 records approved, 3 users nhận notification
  → Type: happy

- TC-BULK-02: Bulk approve — 0 pending
  → Input: admin click "Duyệt tất cả" nhưng không có pending
  → Expected: Message "Không có check-in thủ công nào đang chờ"
  → Type: edge

- TC-API-CHART-01: GET /api/checkins/chart — tháng hiện tại
  → Input: month=2026-03
  → Expected: JSON với daily_hours (31 items), summary, trend
  → Type: happy

- TC-API-LEAVE-01: POST /api/leave/request — valid request
  → Input: {leave_type: "annual", start_date: "2026-03-20", end_date: "2026-03-21", reason: "Việc gia đình"}
  → Expected: 201 Created, leave record trong DB
  → Type: happy

- TC-API-LEAVE-02: POST /api/leave/request — overlap dates
  → Input: dates overlap với leave đã có
  → Expected: 409 Conflict
  → Type: error

### Stream 📊 B + 📝 C — Mini App

- TC-CHART-01: Charts page render — có data
  → Input: user có check-in data tháng này
  → Expected: WorkingHoursChart hiển thị bars, AttendanceDonut hiển thị %
  → Type: happy

- TC-CHART-02: Charts page — tháng không có data
  → Input: month=2025-01 (no data)
  → Expected: Empty state message
  → Type: edge

- TC-NAV-01: Bottom navigation — switch tabs
  → Input: tap từ Dashboard → Charts → Leave
  → Expected: Smooth transition, active tab highlight đúng
  → Type: happy

- TC-LEAVE-FORM-01: Submit leave request — valid
  → Input: fill form hoàn chỉnh, submit
  → Expected: toast thành công, list refresh
  → Type: happy

- TC-LEAVE-FORM-02: Submit leave — not enough annual leave
  → Input: request 15 ngày phép khi chỉ còn 5
  → Expected: Warning message, cho phép submit nhưng hiển thị cảnh báo
  → Type: edge

### Regression

- TC-REG-01: Dashboard vẫn hoạt động sau khi thêm routing
  → Input: mở Mini App
  → Expected: Dashboard load đúng, stats + gamification + history
  → Type: regression

- TC-REG-02: Existing report commands vẫn hoạt động
  → Input: /report today, /report week, /report month
  → Expected: Output đúng format, không error
  → Type: regression

- TC-REG-03: Mini App build thành công
  → Input: `npm run build --prefix miniapp`
  → Expected: Build success, no errors
  → Type: regression

---

## Execution Playbook

### Wave 1 — Backend Enhancement (Sequential ⛓️)

> Stream 🔧 A phải chạy TRƯỚC vì tạo API endpoints mà Mini App streams depend on.

**Streams**: 🔧 A — Backend Enhancement
**Chạy**: Tuần tự, 1 chat

#### Prompt — Stream 🔧 A:

```
Triển khai Stream 🔧 A (Backend Enhancement) trong @TASK_BOARD.md
Đọc section "Context: Codebase Hiện Tại" để hiểu foundation.
Đọc "Conflict Prevention Rules" → chỉ sửa files trong scope.
Ưu tiên P0 trước: A1 → A2 → A5 → A6 → A7, rồi P1: A3 → A4 → A8.
⚠️ API pattern: class handler(BaseHTTPRequestHandler), auth qua auth_service.
⚠️ Overtime: OT chỉ tính sau WORK_END + 30 phút, cap 4 giờ/ngày.
⚠️ Leave API: dùng services/leave_service.py có sẵn, chỉ thêm API endpoints.
⚠️ POST endpoint: auth_service hiện chỉ hỗ trợ GET. Cần extend để support POST (parse body từ self.rfile).
```

**✅ Sau khi Wave 1 xong**:

1. Kiểm tra TASK_BOARD.md → confirm tất cả tasks Wave 1 = ✅
2. Verify: `python3 -m py_compile services/overtime_service.py services/report_service.py api/checkins/chart.py api/leave/request.py api/leave/my.py api/overtime.py bot/handlers/report.py bot/handlers/admin.py`
3. Bắt đầu Wave 2

---

### Wave 2 — Charts + Leave Form (Parallel 🔀)

> Hai streams này làm KHÁC pages/components → chạy SONG SONG an toàn.
> ⚠️ Shared files: api.ts, types/index.ts — Stream 📊 B sửa TRƯỚC, Stream 📝 C đọc lại rồi APPEND.

**Streams**: 📊 B (Charts) + 📝 C (Leave Form)
**Chạy**: Mỗi stream 1 chat riêng, chạy cùng lúc

#### Prompt — Stream 📊 B (Chat 1):

```
Triển khai Stream 📊 B (Mini App Charts) trong @TASK_BOARD.md
Stream 🔧 A đã hoàn thành (Wave 1). Đọc section "Context" + code services mới.
Đọc "Conflict Prevention Rules" → ⚠️ Bạn sửa api.ts + types TRƯỚC stream C.
Cài react-router-dom, recharts.
Làm task B1 → B5 → B2 → B3 (P0), sau đó B4 (P1).
⚠️ Theme: dùng CSS variables từ Telegram (var(--tg-bg), var(--tg-text)...).
⚠️ Chart responsive: width 100%, height auto scale, touch-friendly tooltips.
```

#### Prompt — Stream 📝 C (Chat 2):

```
Triển khai Stream 📝 C (Mini App Leave Form) trong @TASK_BOARD.md
Stream 🔧 A đã hoàn thành (Wave 1). Đọc section "Context" + code services mới.
Đọc "Conflict Prevention Rules" → ⚠️ api.ts + types đã được Stream B sửa. ĐỌC LẠI file trước khi sửa, chỉ APPEND thêm leave functions/types.
Làm task C4 → C1 → C2 → C3 (P0).
⚠️ Form UX: Telegram-native look (haptic feedback, native date picker nếu có).
⚠️ Calculate business days (trừ T7 CN) cho days_count.
```

**✅ Sau khi Wave 2 xong** (cả 2 chat đều hoàn thành):

1. Confirm TASK_BOARD.md → tất cả tasks Wave 2 = ✅
2. Verify: `npm run build --prefix miniapp` — build thành công
3. Check: api.ts không bị conflict (cả 2 streams append đúng)
4. Bắt đầu Wave 3

---

### Wave 3 — Testing & Polish (Sequential ⛓️)

> Stream 🧪 D cần tất cả code sẵn sàng.

**Streams**: 🧪 D — Testing & Polish
**Chạy**: Tuần tự, 1 chat

#### Prompt — Stream 🧪 D:

```
Triển khai Stream 🧪 D (Testing & Polish) trong @TASK_BOARD.md
Tất cả streams Wave 1 + Wave 2 đã hoàn thành. Đọc section "Context" + code mới.
Task D1: fix N+1 query trong api/leaderboard.py (batch load user names).
Task D2: restrict CORS trong services/auth_service.py (dùng MINI_APP_URL).
Task D3: chạy QC theo "QC Test Plan" section trong TASK_BOARD.md.
Task D4: fix bugs phát hiện.
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
Tất cả streams Phase 5 đã xong. Chạy bước 6-7 của /parallel-phase:
- Verify build (py_compile tất cả files mới/sửa)
- npm run build --prefix miniapp
- Confirm TASK_BOARD.md 100%
- Chạy /code-review trên toàn bộ thay đổi phase
- Finalize: gộp changelog, update PROJECT_CONTEXT.md + DEV_ROADMAP.md, commit
```

---

**Status icons:** 📋 TODO → 🔄 IN PROGRESS → ✅ DONE → ⏸️ BLOCKED

**Priority:** P0 (must have) → P1 (should have) → P2 (nice to have)
