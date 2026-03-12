# TASK_BOARD.md — Phase 6: Stabilize & Salary

> **Phase**: 6 — Stabilize & Salary
> **Started**: 2026-03-12
> **Goal**: Fix API lỗi trên mini app, polish UX 3 trang hiện có, tích hợp tính lương

---

## Parallel Execution Strategy

```
              Wave 1 (Sequential ⛓️)     Wave 2 (Parallel 🔀)
Stream 🔧 A  [A1→A2→A3→A4→A5]
Stream 🎨 B                              [B1→B2→B3→B4→B5]
Stream 💰 C                              [C1→C2→C3→C4→C5]
```

| Stream        | Domain          | Tasks | Effort  |
| ------------- | --------------- | ----- | ------- |
| 🔧 A — Fix API & Auth | Backend API | 5     | ~1 ngày |
| 🎨 B — Mini App Polish | Frontend    | 5     | ~1 ngày |
| 💰 C — Salary Integration | Backend + Frontend | 5 | ~2 ngày |

---

## Context: Codebase Hiện Tại

### Backend API (Python, Vercel Serverless)

| File                       | Chức năng                                    |
| -------------------------- | -------------------------------------------- |
| `api/me.py`                | GET /api/me — dashboard data (user, stats)   |
| `api/checkins.py`          | GET /api/checkins, GET /api/checkins/chart    |
| `api/leave.py`             | GET /api/leave/my, POST /api/leave/request   |
| `api/leaderboard.py`       | GET /api/leaderboard — top 10 + user rank    |
| `services/auth_service.py` | Telegram initData HMAC-SHA256 validation     |
| `services/leave_service.py`| Leave CRUD, business days, balance           |
| `services/gamification_service.py` | Points, streak, leaderboard         |
| `services/report_service.py` | is_late(), daily/weekly/monthly reports     |
| `db/client.py`             | PostgREST REST wrapper (httpx)               |

### Mini App (React 18 + Vite + Tailwind)

| File                         | Chức năng                        |
| ---------------------------- | -------------------------------- |
| `miniapp/src/App.tsx`        | Router + BottomNav               |
| `miniapp/src/lib/api.ts`    | API client (apiFetch + functions)|
| `miniapp/src/types/index.ts` | TypeScript types + constants     |
| `miniapp/src/contexts/TelegramContext.tsx` | Auth + profile context |
| `miniapp/src/pages/Dashboard.tsx` | Stats + History                |
| `miniapp/src/pages/Charts.tsx`    | Working hours chart + trend    |
| `miniapp/src/pages/Leave.tsx`     | Leave list + form              |

### Database Schema (Supabase PostgreSQL)

10 tables: `users`, `offices`, `wifi_whitelist`, `nfc_tokens`, `qr_sessions`, `checkins`, `leaves`, `gamification`, `point_transactions`, `system_config`.

> 🔑 **Quan trọng**: `is_ontime` column trên `checkins` table chỉ set khi check-in, KHÔNG thay đổi từ `_get_checkin_stats_this_month()`.

### Root Cause Analysis — HTTP 500 Errors

**Bug 1: `/api/me` → Dashboard blank**

`_get_checkin_stats_this_month()` returns `{total, ontime, late, wfh}` nhưng TypeScript `CheckinStats` type mong đợi `{total_days, late_days, wfh_days, leave_days, ontime_percentage}`.

Dashboard component gọi `profile?.checkin_stats.total_days` → nhận `undefined` → NaN hiển thị.

Ngoài ra, `gamification` response: `get_user_stats()` trả `None` nếu user chưa có record gamification → cần handle.

**Bug 2: `/api/checkins/chart` → Thống kê blank**

Khả năng lỗi nằm ở `is_late()` function hoặc PostgREST filter format. Cần debug thực tế trên production.

**Bug 3: `/api/leave/my` → "string did not match expected pattern"**

Lỗi PostgREST filter `start_date.gte` / `start_date.lt` trả lỗi pattern khi `year` param. Pattern date filter cần verify format.

---

## 🔧 Stream A — Fix API & Auth (P0)

> **Goal**: 3 API endpoints hoạt động đúng, Mini App hiển thị data trên Telegram
> **Domain**: `api/`, `services/`
> **Priority**: P0 — phải xong trước khi Mini App Polish

| #  | Task | Priority | Status | Description |
| -- | ---- | -------- | ------ | ----------- |
| A1 | Fix `/api/me` response format | P0 | ✅ | Sửa field names: `total→total_days`, `ontime→ontime`, `late→late_days`, `wfh→wfh_days`. Thêm `leave_days`, `ontime_percentage`. Handle `get_user_stats()` returns None. |
| A2 | Fix `/api/checkins/chart` | P0 | ✅ | Debug + fix chart data endpoint. Verify `is_late()` function, PostgREST filters, timezone handling. |
| A3 | Fix `/api/leave/my` pattern error | P0 | ✅ | Fix PostgREST date filter format cho `get_user_leaves()`. Verify `start_date.gte` filter pattern. |
| A4 | Verify initData auth flow E2E | P0 | ✅ | Test HMAC-SHA256 validation end-to-end: Mini App → API → validate → response. Verify `MAX_AUTH_AGE_SECONDS`. |
| A5 | Add detailed error logging | P1 | ✅ | Thêm structured logging với request info (telegram_id, path, params) cho mỗi API endpoint. Return error detail cho frontend debug. |

### Acceptance Criteria — Stream A

- [x] `GET /api/me` trả đúng format `{total_days, late_days, wfh_days, leave_days, ontime_percentage}` → Dashboard hiển thị số
- [x] `GET /api/checkins/chart` trả daily_hours + summary + trend → Charts page render biểu đồ
- [x] `GET /api/leave/my` trả leaves + balance → Leave page hiển thị list
- [x] Auth reject với error message cụ thể (expired/invalid/missing) thay vì generic 401
- [x] Tất cả 3 API trả `{ok: true, ...data}` khi success, `{ok: false, error: "message"}` khi fail

---

## 🎨 Stream B — Mini App Polish (P1)

> **Goal**: UX nhất quán, error handling tốt, loading states đẹp trên tất cả 3 trang
> **Domain**: `miniapp/src/`
> **Depends on**: Stream A (Wave 1)

| #  | Task | Priority | Status | Description |
| -- | ---- | -------- | ------ | ----------- |
| B1 | Error handling cụ thể | P1 | ✅ | Hiển thị error message từ API thay vì generic "HTTP 500". Phân biệt 401 (auth)/404 (not found)/500 (server error). Retry button. |
| B2 | Empty states UI | P1 | ✅ | UI đẹp khi chưa có data (first-time user): no checkins, no leaves, no chart data. Illustrations + hướng dẫn. |
| B3 | Loading skeleton nhất quán | P2 | ✅ | Verify skeleton components render đúng kích thước trên cả 3 trang. Fix nếu shimmer animation bị giật. |
| B4 | Offline fallback & retry | P2 | ✅ | Detect offline state, show Toast. Retry logic với exponential backoff. Cache last successful response. |
| B5 | Dark/light mode test | P2 | ✅ | Verify Telegram theme vars (`--tg-*`) work cả dark và light theme. Fix contrast issues. |

### Acceptance Criteria — Stream B

- [x] Error state hiển thị icon + message cụ thể + nút "Thử lại" trên cả 3 trang
- [x] Empty state hiển thị illustration hướng dẫn thay vì blank/loading vĩnh viễn
- [x] Skeleton loading smooth, không giật khi chuyển trang
- [x] Khi offline: Toast "Không có kết nối" + auto retry khi có mạng lại
- [x] Dark mode: text đọc được, contrast đủ, không có element bị "biến mất"

---

## 💰 Stream C — Salary Integration (High)

> **Goal**: Nhân viên xem lương ước tính trên Mini App (basic salary + OT + deductions)
> **Domain**: `services/`, `api/`, `miniapp/src/`, `db/`
> **Depends on**: Stream A (Wave 1)

| #  | Task | Priority | Status | Description |
| -- | ---- | -------- | ------ | ----------- |
| C1 | Salary calculation service | P0 | ✅ | Tạo `services/salary_service.py`: tính lương = basic + OT allowance - late deductions - unpaid leave. Config trong `system_config` table. |
| C2 | Salary API endpoint | P0 | ✅ | Tạo `api/salary.py`: GET `/api/salary?month=YYYY-MM` → monthly salary summary. Auth + CORS. |
| C3 | Mini App: Salary page/tab | P1 | ✅ | Tạo component Salary trong Mini App: monthly view, breakdown (basic, OT, deductions), status badge. |
| C4 | Salary Excel export | P2 | ✅ | API endpoint export salary as Excel (for admin/HR). |
| C5 | Wire salary into Mini App | P1 | ✅ | Thêm route + nav + API client. Integrate salary page vào app flow. Seed salary config data. |

### Acceptance Criteria — Stream C

- [x] `salary_service.py` tính đúng: basic_salary + (OT_minutes / 60 * OT_rate) - (late_deductions) - (unpaid_leave * daily_rate)
- [x] `GET /api/salary` trả response format chuẩn với breakdown chi tiết
- [x] Salary page render đúng tháng, hiển thị breakdown, tổng lương
- [x] Admin export Excel bảng lương tháng
- [x] Salary tab xuất hiện trên Bottom Nav, navigate smooth

---

## Cross-Stream Dependencies

### Dependency Map

| Task | Depends on | Type | Notes |
| ---- | ---------- | ---- | ----- |
| B1-B5 | A1-A3 | cross-stream | Polish UX cần API trả đúng data trước |
| C2 | C1 | intra-stream | API gọi salary service |
| C3 | C2, C5 | intra-stream | UI cần API endpoint + routing |
| C5 | C3 | intra-stream | Wire cần component đã tạo |
| B4 | B1 | intra-stream | Retry logic dùng error handling từ B1 |

### Execution Order

1. 🔧 **Stream A** → chạy **trước** (Wave 1 — fix foundation, API phải OK trước)
2. 🎨 **Stream B** + 💰 **Stream C** → chạy **song song** (Wave 2 — sau A xong)

---

## Conflict Prevention Rules

### Shared Files

| File | Stream | Tasks | Rule |
| ---- | ------ | ----- | ---- |
| `miniapp/src/types/index.ts` | 🎨 B + 💰 C | B1-B5, C3-C5 | Stream B sửa trước (chỉ fix existing types). Stream C thêm Salary types SAU B. |
| `miniapp/src/lib/api.ts` | 🎨 B + 💰 C | B1, C5 | Stream B update error handling. Stream C thêm `fetchSalary()` SAU B. |
| `miniapp/src/App.tsx` | 💰 C | C5 | Chỉ Stream C sửa (thêm route). |
| `miniapp/src/components/BottomNav.tsx` | 💰 C | C5 | Chỉ Stream C sửa (thêm tab Lương). |
| `services/auth_service.py` | 🔧 A | A5 | Chỉ Stream A sửa (error logging). |
| `vercel.json` | 💰 C | C2 | Chỉ Stream C sửa (thêm salary rewrite nếu cần). |

### Merge Strategy

- Mỗi stream KHÔNG commit riêng — gộp commit ở bước Finalize
- Nếu 2 streams cùng cần sửa 1 file → stream chạy SAU phải đọc lại file trước khi sửa
- Sync point: sau mỗi wave hoàn thành → verify trước khi bắt đầu wave tiếp
- Stream B sửa shared files TRƯỚC Stream C

---

## Progress Summary

| Stream | Total | Done | In Progress | Blocked | % |
| ------ | ----- | ---- | ----------- | ------- | - |
| 🔧 A — Fix API & Auth | 5 | 5 | 0 | 0 | 100% |
| 🎨 B — Mini App Polish | 5 | 5 | 0 | 0 | 100% |
| 💰 C — Salary Integration | 5 | 5 | 0 | 0 | 100% |
| **Tổng** | **15** | **15** | **0** | **0** | **100%** |

---

## QC Test Plan

### Stream A — Fix API & Auth

| # | Test Case | Type | Expected Result |
| - | --------- | ---- | --------------- |
| QC-A1 | Mở miniapp từ Telegram → Dashboard hiển thị stats | E2E | 4 stat cards có số, không NaN/undefined |
| QC-A2 | Navigate sang Charts → biểu đồ render | E2E | Working hours chart + donut + trend |
| QC-A3 | Navigate sang Leave → danh sách nghỉ | E2E | Leave list + balance card hiển thị |
| QC-A4 | Gửi initData expired (>1h) → reject | Unit | 401 Unauthorized + message "Token expired" |
| QC-A5 | Gửi initData invalid hash → reject | Unit | 401 Unauthorized + message "Invalid signature" |

### Stream B — Mini App Polish

| # | Test Case | Type | Expected Result |
| - | --------- | ---- | --------------- |
| QC-B1 | Disconnect WiFi → mở miniapp | E2E | Toast "Không có kết nối" + retry option |
| QC-B2 | First-time user (no checkins) → Dashboard | E2E | Empty state illustration + hướng dẫn |
| QC-B3 | Switch Telegram sang dark mode → mở miniapp | E2E | Tất cả text visible, contrast OK |
| QC-B4 | Chuyển tab nhanh liên tục | E2E | Skeleton loading smooth, không flash |

### Stream C — Salary Integration

| # | Test Case | Type | Expected Result |
| - | --------- | ---- | --------------- |
| QC-C1 | GET /api/salary → monthly summary | API | Response: basic + OT + deductions + total |
| QC-C2 | Salary page → hiển thị breakdown | E2E | Cards: Lương cơ bản, OT, Khấu trừ, Tổng |
| QC-C3 | Export salary Excel | API | File .xlsx download OK, data đúng |

---

## Execution Playbook

### Wave 1 — Fix API & Auth (Sequential ⛓️)

> Stream phải chạy TRƯỚC vì API là foundation cho Mini App.

**Streams**: 🔧 A
**Chạy**: 1 chat

#### Prompt — Stream 🔧 A:

> Triển khai Stream 🔧 A (Fix API & Auth) trong @TASK_BOARD.md
> Đọc section "Context: Codebase Hiện Tại" và "Root Cause Analysis" để hiểu bugs.
> Làm từ task A1 (P0) trước. Mỗi task xong → update status 📋 → ✅.

**✅ Sau khi Wave 1 xong**: Kiểm tra TASK_BOARD.md → confirm tất cả tasks Wave 1 = ✅, rồi bắt đầu Wave 2.

---

### Wave 2 — Polish & Salary (Parallel 🔀)

> Các streams này KHÔNG depend nhau → chạy SONG SONG (2 chats riêng).

**Streams**: 🎨 B + 💰 C
**Chạy**: Mỗi stream 1 chat riêng, chạy cùng lúc

#### Prompt — Stream 🎨 B (Chat 1):

> Triển khai Stream 🎨 B (Mini App Polish) trong @TASK_BOARD.md
> Stream 🔧 A đã hoàn thành (Wave 1). Đọc section "Context" + Root Cause Analysis để hiểu.
> Làm từ task B1 (P1) trước. Check "Conflict Prevention Rules" trước khi sửa shared files.

#### Prompt — Stream 💰 C (Chat 2):

> Triển khai Stream 💰 C (Salary Integration) trong @TASK_BOARD.md
> Stream 🔧 A đã hoàn thành (Wave 1). Đọc section "Context" để hiểu codebase.
> Làm từ task C1 (P0) trước. Check "Conflict Prevention Rules" — sửa shared files SAU Stream B.

**✅ Sau khi Wave 2 xong**: Cả 2 chat đều xong → mở chat mới chạy bước 6 (Verify & Review).

---

### Nối tiếp stream (nếu 1 chat bị ngắt):

> Tiếp tục Stream [X] trong @TASK_BOARD.md — các task X1, X2 đã xong (✅), tiếp từ X3.

### Sau khi TẤT CẢ waves xong:

> Tất cả streams Phase 6 đã xong. Chạy bước 6-7 của /parallel-phase:
>
> - Verify build
> - Confirm TASK_BOARD.md 100%
> - Chạy /code-review trên toàn bộ thay đổi phase
> - Finalize: gộp changelog, update docs, commit
