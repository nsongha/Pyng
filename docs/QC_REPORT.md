# QC Report — Phase 5: Enhancement (v0.5.0)

> Generated: 2026-03-11
> Version: v0.5.0 · Branch: main

## 1. Compile Check — Python Files (Phase 5 New/Modified)

| File | Status |
|------|--------|
| `services/overtime_service.py` [NEW] | ✅ OK |
| `services/report_service.py` [MOD] | ✅ OK |
| `services/auth_service.py` [MOD - D2 CORS fix] | ✅ OK |
| `api/checkins/chart.py` [NEW] | ✅ OK |
| `api/leave/request.py` [NEW] | ✅ OK |
| `api/leave/my.py` [NEW] | ✅ OK |
| `api/overtime.py` [NEW] | ✅ OK |
| `api/leaderboard.py` [MOD - D1 N+1 fix] | ✅ OK |
| `bot/handlers/report.py` [MOD] | ✅ OK |
| `bot/handlers/admin.py` [MOD] | ✅ OK |

**Result**: 10/10 files compile thành công.

## 2. Miniapp Build Check

```
npm run build --prefix miniapp
tsc -b && vite build
✓ 712 modules transformed, built in 1.84s
```

**Result**: ✅ Build success. 712 modules (bao gồm recharts, react-router-dom mới).

## 3. Tech Debt Fixes

### TD-001: N+1 query trong leaderboard API — ✅ FIXED

**File**: `api/leaderboard.py` L34-45
**Before**: `db.select("users")` per leaderboard entry (N queries cho N users)
**After**: Batch query 1 lần → build `name_map` → enrich. Copy pattern từ `bot/handlers/gamification.py`.
**Impact**: Giảm từ 10 DB queries xuống 1 query cho leaderboard endpoint.

### TD-002: CORS wildcard cho Mini App API — ✅ FIXED

**File**: `services/auth_service.py` L170-177, L199, L213
**Before**: `Access-Control-Allow-Origin: *` hardcoded
**After**: `_get_cors_origin()` → `MINI_APP_URL` if set, fallback `*` cho dev.
**Impact**: Production restrict CORS tới `https://pyng.vercel.app` qua env var.

## 4. Code Path Trace — New API Endpoints

### GET /api/checkins/chart (314 lines)
```
Request → @require_auth → parse month param → _get_chart_data()
  → query checkins (type=in) + checkouts (type=out) by date range
  → pair by date → calculate hours per day
  → summary: avg_hours, total_days, ontime_rate, most_used_method
  → trend: compare với tháng trước via _get_month_avg_hours()
  → json_api_response(200, {daily_hours, summary, trend})
```

### POST /api/leave/request (196 lines)
```
Request → @require_auth → parse_request_body()
  → _validate_leave_request(): type check, date parse, overlap check
  → create_leave_request() via leave_service
  → _notify_admin_leave_request() (async, fire-and-forget)
  → json_api_response(201, {leave})
```

### GET /api/leave/my (73 lines)
```
Request → @require_auth → parse year param
  → get_user_leaves(user_id, year) → leaves list
  → get_remaining_leave_days(user_id) → balance
  → json_api_response(200, {leaves, balance})
```

### GET /api/overtime (74 lines)
```
Request → @require_auth → parse month param
  → get_monthly_overtime(user_id, month, year)
    → iterate weekdays → calculate_overtime() per day
    → sum sessions where has_overtime=True
  → json_api_response(200, {total_minutes, total_days, sessions})
```

## 5. QC Test Plan Verification (Static Analysis)

| Test Case | Type | Verified |
|-----------|------|----------|
| TC-OT-01: OT 45 phút (checkout 19:00) | happy | ✅ Logic correct (19:00 - 18:15 = 45) |
| TC-OT-02: No OT (checkout 18:00, grace) | edge | ✅ checkout <= threshold → 0 |
| TC-OT-03: OT cap 4h (checkout 23:30) | edge | ✅ `min(ot_minutes, OT_CAP_MINUTES=240)` |
| TC-RPT-01: Custom range report | happy | ✅ `generate_custom_range_excel(start, end)` |
| TC-RPT-02: Range >90 days reject | error | ✅ L291: `if range_days > 90` |
| TC-BULK-01: Bulk approve 3 pending | happy | ✅ Bot handler iterates + approves + notifies |
| TC-BULK-02: 0 pending bulk | edge | ✅ Empty check → "Không có..." message |
| TC-API-CHART-01: Chart data | happy | ✅ Returns daily_hours + summary + trend |
| TC-API-LEAVE-01: Valid leave request | happy | ✅ Validation → create → notify → 201 |
| TC-API-LEAVE-02: Overlap dates | error | ✅ L82: overlap detection → 409 |
| TC-CHART-01: Charts page render | happy | ✅ Build success, components present |
| TC-NAV-01: Bottom navigation | happy | ✅ BottomNav.tsx, react-router-dom |
| TC-REG-01: Dashboard still works | regression | ✅ Build success, Dashboard.tsx intact |
| TC-REG-02: Report commands | regression | ✅ Compile OK, handler patterns preserved |
| TC-REG-03: Miniapp build success | regression | ✅ 712 modules, 1.84s |

## 6. Bugs Phát Hiện

| # | Severity | Description | Status |
|---|----------|-------------|--------|
| — | — | Không phát hiện bug P0/P1 mới | ✅ Clean |

> Bundle size warning (>500KB) do recharts — acceptable cho internal tool. Có thể code-split nếu cần optimize sau.

## 7. Kết quả

| Hạng mục | Kết quả |
|----------|---------|
| Python compile | 10/10 ✅ |
| Miniapp build | ✅ (712 modules) |
| Tech debt D1 (N+1) | ✅ Fixed |
| Tech debt D2 (CORS) | ✅ Fixed |
| P0 bugs | 0 found ✅ |
| P1 bugs | 0 found ✅ |
| Test cases verified | 15/15 ✅ |

## 8. Release Checklist

- [x] Tất cả Python files compile thành công (10/10)
- [x] Miniapp build thành công (712 modules)
- [x] No critical bugs blocking release
- [x] Tech debt TD-001 + TD-002 resolved
- [x] Env vars: `MINI_APP_URL` cần set cho production CORS
- [x] Database: không có migration mới
- [x] Dependencies: `requirements.txt` không đổi, `miniapp/package.json` thêm recharts + react-router-dom
- [x] KNOWN_ISSUES.md cập nhật (TD-001, TD-002 resolved)
- [ ] Deploy lên Vercel và verify miniapp hoạt động
- [ ] Test bot trên Telegram staging
