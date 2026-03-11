# Phase 2 Task Board — Check-in Methods (v0.2.0)

> 🎯 Mục tiêu: Thêm QR Code + NFC + Manual Fallback check-in
> Version target: v0.2.0

## Thuật ngữ

- **Stream**: Nhóm tasks theo domain/concern — mỗi stream chạy trong 1 conversation riêng
- **Wave**: Đợt chạy, gộp 1+ streams cùng execution order (sequential trước, parallel sau)

## Parallel Execution Strategy

Phase này có **15 tasks** chia **3 streams**, **2 waves**:

| Stream                 | Domain                          | Scope                                          | Wave |
| ---------------------- | ------------------------------- | ---------------------------------------------- | ---- |
| 🎫 **QR System**       | Services + Bot + API + Frontend | `services/`, `bot/handlers/`, `api/qr/`, `qr/` | 1    |
| 🏷️ **NFC System**      | Services + Bot + Admin          | `services/`, `bot/handlers/`                   | 2    |
| 📸 **Manual Fallback** | Bot + Admin                     | `bot/handlers/`                                | 2    |

**Execution order**: 🎫 QR System (Wave 1) → 🏷️ NFC + 📸 Manual (Wave 2, song song)

> **Lý do QR đi trước**: QR handler cần sửa `/start` deep link logic. NFC cũng dùng deep link tương tự nhưng pattern đã được QR thiết lập, nên NFC đi sau sẽ đơn giản hơn.

---

## Context: Codebase Hiện Tại

### Tech Stack

- **Backend**: Python 3.11+ / python-telegram-bot v21.5 (async webhook)
- **Database**: Supabase PostgreSQL (PostgREST API qua httpx, KHÔNG dùng SDK)
- **Deploy**: Vercel Serverless (auto-deploy từ GitHub)
- **Scheduler**: GitHub Actions Cron
- **Version hiện tại**: v0.1.0 (Phase 1 hoàn thành)

### Foundation Available

- `db/client.py` — REST wrapper (select, insert, update, delete) qua PostgREST API
- `db/schema.sql` — Đã có sẵn tables: `qr_sessions`, `nfc_tokens`, `checkins` (method supports 'qr'|'nfc'|'manual')
- `services/checkin_service.py` — `create_checkin()`, `has_checked_in_today()`, `get_today_checkin()`
- `services/office_service.py` — `get_active_office()`
- `services/user_service.py` — `register_user()`, `get_by_telegram_id()`
- `bot/handlers/_helpers.py` — `get_active_user_or_none()`, `get_ontime_status()`, `format_current_time()`
- `bot/handlers/checkin.py` — Re-export module, `get_checkin_handlers()` tập hợp tất cả handlers
- `bot/handlers/start.py` — `/start` registration flow (ConversationHandler) — **CHƯA xử lý deep link args**
- `bot/app.py` — Application factory, đăng ký handlers
- `config/settings.py` — `QR_EXPIRE_SECONDS=300`, `QR_DISPLAY_URL`, `ADMIN_TELEGRAM_IDS`, `ADMIN_GROUP_ID`
- `qr/index.html` — QR display page (placeholder, TODO fetch từ API)
- `requirements.txt` — `qrcode[pil]` và `Pillow` đã ghi sẵn (commented) chờ uncomment

### DB Schema sẵn có

```sql
-- QR Sessions (sẵn)
CREATE TABLE qr_sessions (
    id SERIAL PRIMARY KEY,
    token VARCHAR(100) UNIQUE NOT NULL,
    office_id INT REFERENCES offices(id),
    created_at TIMESTAMP DEFAULT NOW(),
    expire_at TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT FALSE
);

-- NFC Tokens (sẵn)
CREATE TABLE nfc_tokens (
    id SERIAL PRIMARY KEY,
    token VARCHAR(100) UNIQUE NOT NULL,
    office_id INT REFERENCES offices(id),
    location VARCHAR(200),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Checkins (sẵn — method đã support 'qr', 'nfc', 'manual')
-- is_manual_approved BOOLEAN, approved_by BIGINT
```

### API Endpoints Available

| Method | Path                | Mô tả                         |
| ------ | ------------------- | ----------------------------- |
| POST   | `/api/webhook`      | Nhận Telegram webhook updates |
| GET    | `/api/cron/morning` | Nhắc check-in 08:30           |
| GET    | `/api/cron/evening` | Nhắc check-out 17:45          |

### Patterns cần tuân theo

1. **Handler pattern**: Mỗi handler file export hàm `get_xxx_handler()` hoặc `get_xxx_handlers()`
2. **Service pattern**: Business logic trong `services/`, KHÔNG trong handler
3. **DB pattern**: Dùng `db.client` (select/insert/update/delete), KHÔNG import httpx trực tiếp
4. **Deep link**: `/start qr_TOKEN` → `context.args = ["qr_TOKEN"]` (python-telegram-bot tự parse)
5. **Admin check**: Dùng `ADMIN_TELEGRAM_IDS` hoặc kiểm tra `user["role"] == "admin"`

---

## Stream 🎫 A — QR System

**Owner**: Services + Bot + API + Frontend
**Scope**: `services/qr_service.py`, `bot/handlers/qr_checkin.py`, `bot/handlers/start.py`, `api/qr/`, `qr/index.html`, `bot/handlers/checkin.py`, `bot/app.py`, `requirements.txt`, `config/settings.py`

| #   | Task                           | Status | Priority | Dependencies | Files affected                          |
| --- | ------------------------------ | ------ | -------- | ------------ | --------------------------------------- |
| A1  | Uncomment QR dependencies      | ✅     | P0       | —            | `requirements.txt`                      |
| A2  | QR Service (CRUD + generate)   | ✅     | P0       | A1           | `services/qr_service.py` [NEW]          |
| A3  | QR API endpoint                | ✅     | P0       | A2           | `api/qr/current.py` [NEW]               |
| A4  | QR display page (auto-refresh) | ✅     | P0       | A3           | `qr/index.html`                         |
| A5  | Deep link handler (start.py)   | ✅     | P0       | A2           | `bot/handlers/start.py`                 |
| A6  | QR checkin handler             | ✅     | P0       | A2, A5       | `bot/handlers/qr_checkin.py` [NEW]      |
| A7  | Register QR handlers           | ✅     | P0       | A6           | `bot/handlers/checkin.py`, `bot/app.py` |
| A8  | Admin QR config                | ✅     | P1       | A2           | `bot/handlers/admin.py`                 |

**Acceptance Criteria:**

- A1: `qrcode[pil]==7.4.2` và `Pillow==10.2.0` uncommented + verify `pip install -r requirements.txt` pass
- A2: `create_qr_session()` tạo token unique, lưu DB với expire 5p. `validate_qr_token()` check tồn tại + chưa used + chưa expired. `generate_qr_image()` trả về PNG bytes. `get_current_qr()` trả về QR đang active. `cleanup_expired_qr()` xóa QR quá hạn.
- A3: `GET /api/qr/current` trả về QR image (PNG) hoặc JSON `{token, expire_at, qr_url}`. Cron endpoint `GET /api/cron/qr_refresh.py` tạo QR mới mỗi 5 phút (giờ làm việc)
- A4: `qr/index.html` fetch từ `/api/qr/current` mỗi 30s, hiển thị QR image + countdown timer. Deep link URL hiển thị dưới QR (fallback nếu scan không được)
- A5: `/start qr_TOKEN` → validate token → check-in nếu hợp lệ. `/start nfc_TOKEN` → parse nhưng chưa xử lý (để Stream B). Backward compatible — `/start` không args vẫn chạy registration flow
- A6: `/checkin_qr` command cho manual input (gõ mã 6 ký tự). `handle_qr_deeplink()` xử lý logic sau khi parse deep link
- A7: Thêm QR handlers vào `get_checkin_handlers()` và `create_bot()`
- A8: Admin xem QR display link, config expire time (optional, P1)

---

## Stream 🏷️ B — NFC System

**Owner**: Services + Bot + Admin
**Scope**: `services/nfc_service.py`, `bot/handlers/nfc_checkin.py`, `bot/handlers/start.py`, `bot/handlers/admin.py`, `bot/handlers/checkin.py`

| #   | Task                              | Status | Priority | Dependencies   | Files affected                                                   |
| --- | --------------------------------- | ------ | -------- | -------------- | ---------------------------------------------------------------- |
| B1  | NFC Service (CRUD + validate)     | ✅     | P0       | A5 (deep link) | `services/nfc_service.py` [NEW]                                  |
| B2  | NFC checkin handler               | ✅     | P0       | B1, A5         | `bot/handlers/nfc_checkin.py` [NEW]                              |
| B3  | Register NFC handlers + deep link | ✅     | P0       | B2             | `bot/handlers/checkin.py`, `bot/handlers/start.py`, `bot/app.py` |
| B4  | Admin NFC management              | ✅     | P1       | B1             | `bot/handlers/admin.py`                                          |

**Acceptance Criteria:**

- B1: `create_nfc_token()` tạo token lưu DB. `validate_nfc_token()` check tồn tại + is_active. `list_nfc_tokens()` cho admin. `deactivate_nfc_token()` vô hiệu hóa
- B2: `handle_nfc_deeplink()` validate token → check-in nếu hợp lệ. Error messages rõ ràng (token hết hạn, không hợp lệ...)
- B3: Deep link `/start nfc_TOKEN` → route tới NFC handler. Thêm vào `get_checkin_handlers()` + `create_bot()`
- B4: `/admin_nfc` → tạo NFC token mới, xem danh sách, vô hiệu hóa token. Hiển thị deep link URL cho mỗi token (để ghi vào NFC tag)

---

## Stream 📸 C — Manual Fallback

**Owner**: Bot + Admin
**Scope**: `bot/handlers/manual_checkin.py`, `bot/handlers/admin.py`, `bot/handlers/checkin.py`, `bot/app.py`

| #   | Task                                | Status | Priority | Dependencies | Files affected                          |
| --- | ----------------------------------- | ------ | -------- | ------------ | --------------------------------------- |
| C1  | Manual checkin handler (selfie)     | ✅     | P0       | —            | `bot/handlers/manual_checkin.py` [NEW]  |
| C2  | Admin notification + approve/reject | ✅     | P0       | C1           | `bot/handlers/admin.py`                 |
| C3  | Register manual handlers            | ✅     | P0       | C1, C2       | `bot/handlers/checkin.py`, `bot/app.py` |

**Acceptance Criteria:**

- C1: `/manual` hoặc `/checkin_manual` → ConversationHandler: hỏi lý do → nhận ảnh selfie → lưu pending. Validate file size. Hiển thị thông báo "Đang chờ admin duyệt..."
- C2: Admin nhận notification với ảnh + lý do. Inline buttons "Duyệt" / "Từ chối". Duyệt → tạo checkin record (method='manual', is_manual_approved=true). Từ chối → gửi lý do cho user
- C3: Thêm manual handlers vào `get_checkin_handlers()` + `create_bot()`

---

## Cross-Stream Dependencies

### Dependency Map

| Task | Depends on | Type         | Notes                                                 |
| ---- | ---------- | ------------ | ----------------------------------------------------- |
| A2   | A1         | in-stream    | QR service cần qrcode+Pillow packages                 |
| A3   | A2         | in-stream    | API endpoint gọi qr_service                           |
| A4   | A3         | in-stream    | Frontend fetch từ API                                 |
| A5   | A2         | in-stream    | Deep link cần qr_service validate                     |
| A6   | A2, A5     | in-stream    | QR checkin dùng service + deep link                   |
| A7   | A6         | in-stream    | Register sau khi handler xong                         |
| B1   | A5         | cross-stream | NFC cần deep link routing pattern đã thiết lập bởi QR |
| B2   | B1, A5     | cross-stream | NFC handler cần service + deep link từ Wave 1         |
| B3   | B2         | in-stream    | Register sau khi handler xong                         |
| C1   | —          | independent  | Manual không depend stream nào                        |
| C2   | C1         | in-stream    | Admin approve cần manual handler gửi notification     |
| C3   | C1, C2     | in-stream    | Register sau khi handlers xong                        |

### Execution Order

1. **Wave 1** (Sequential ⛓️): 🎫 Stream A (QR System) — thiết lập deep link pattern + QR infrastructure
2. **Wave 2** (Parallel 🔀): 🏷️ Stream B (NFC) + 📸 Stream C (Manual) — independent, chạy song song

---

## Conflict Prevention Rules

### Shared Files

| File                      | Streams dùng     | Tasks      | Rule                                                                                         |
| ------------------------- | ---------------- | ---------- | -------------------------------------------------------------------------------------------- |
| `bot/handlers/start.py`   | 🎫 A, 🏷️ B       | A5, B3     | Stream A sửa TRƯỚC (thêm deep link routing). Stream B chỉ thêm NFC case vào existing routing |
| `bot/handlers/checkin.py` | 🎫 A, 🏷️ B, 📸 C | A7, B3, C3 | Stream A sửa TRƯỚC. Stream B + C đọc lại rồi thêm import                                     |
| `bot/app.py`              | 🎫 A, 🏷️ B, 📸 C | A7, B3, C3 | Stream A sửa TRƯỚC. Stream B + C đọc lại rồi thêm handlers                                   |
| `bot/handlers/admin.py`   | 🎫 A, 🏷️ B, 📸 C | A8, B4, C2 | Mỗi stream thêm section mới (append). Tránh sửa code cũ                                      |
| `requirements.txt`        | 🎫 A             | A1         | Chỉ Stream A sửa ở Wave 1                                                                    |
| `config/settings.py`      | 🎫 A             | —          | Chỉ đọc, KHÔNG sửa (đã có QR_EXPIRE_SECONDS, QR_DISPLAY_URL)                                 |

### Merge Strategy

- Mỗi stream KHÔNG commit riêng — gộp commit ở bước Finalize
- Nếu 2 streams cùng cần sửa 1 file → stream chạy SAU phải đọc lại file trước khi sửa
- Sync point: sau Wave 1 hoàn thành → verify trước khi bắt đầu Wave 2
- **Shared file strategy cho `bot/handlers/start.py`**:
  - Wave 1 (Stream A): Thêm `_handle_deep_link()` function + if/elif routing (qr case)
  - Wave 2 (Stream B): Đọc lại file → thêm `elif args[0].startswith("nfc_")` vào existing routing

---

## Progress Summary

| Stream        | Total  | Done   | Remaining | %        |
| ------------- | ------ | ------ | --------- | -------- |
| 🎫 A (QR)     | 8      | 8      | 0         | 100%     |
| 🏷️ B (NFC)    | 4      | 4      | 0         | 100%     |
| 📸 C (Manual) | 3      | 3      | 0         | 100%     |
| **All**       | **15** | **15** | **0**     | **100%** |

---

## Execution Playbook

### Wave 1 — QR System (Sequential ⛓️)

> Stream 🎫 A phải chạy TRƯỚC vì thiết lập deep link pattern + QR infrastructure.

**Streams**: 🎫 A — QR System
**Chạy**: Tuần tự, 1 chat

#### Prompt — Stream 🎫 A:

```
Triển khai Stream 🎫 A (QR System) trong @TASK_BOARD.md
Đọc section "Context: Codebase Hiện Tại" để hiểu foundation.
Đọc "Conflict Prevention Rules" → chỉ sửa files trong scope.
Làm từ task P0 trước (A1 → A2 → A3 → A4 → A5 → A6 → A7), sau đó P1 (A8).
```

**✅ Sau khi Wave 1 xong**:

1. Kiểm tra TASK_BOARD.md → confirm tất cả tasks Wave 1 = ✅
2. Verify: `python3 -m py_compile services/qr_service.py bot/handlers/qr_checkin.py bot/handlers/start.py api/qr/current.py`
3. Bắt đầu Wave 2

---

### Wave 2 — NFC + Manual (Parallel 🔀)

> Các streams này KHÔNG depend nhau → chạy SONG SONG trong chat riêng.

**Streams**: 🏷️ B (NFC) + 📸 C (Manual)
**Chạy**: Mỗi stream 1 chat riêng, chạy cùng lúc

#### Prompt — Stream 🏷️ B (Chat 1):

```
Triển khai Stream 🏷️ B (NFC System) trong @TASK_BOARD.md
Stream 🎫 A (QR System) đã hoàn thành (Wave 1). Đọc section "Context" + code mới trong start.py
Đọc "Conflict Prevention Rules" → chỉ sửa files trong scope.
Đọc lại bot/handlers/start.py vì Wave 1 đã sửa (thêm deep link routing).
Làm từ task P0 trước (B1 → B2 → B3), sau đó P1 (B4).
```

#### Prompt — Stream 📸 C (Chat 2):

```
Triển khai Stream 📸 C (Manual Fallback) trong @TASK_BOARD.md
Stream 🎫 A (QR System) đã hoàn thành (Wave 1). Đọc section "Context" + code mới.
Đọc "Conflict Prevention Rules" → chỉ sửa files trong scope.
Đọc lại bot/handlers/checkin.py và bot/app.py vì Wave 1 đã sửa.
Làm task C1 → C2 → C3.
```

**✅ Sau khi Wave 2 xong** (cả 2 chat đều hoàn thành):

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
Tất cả streams Phase 2 đã xong. Chạy bước 6-7 của /parallel-phase:
- Verify build (py_compile tất cả files mới/sửa)
- Confirm TASK_BOARD.md 100%
- Chạy /code-review trên toàn bộ thay đổi phase
- Finalize: gộp changelog, update PROJECT_CONTEXT.md + DEV_ROADMAP.md, commit
```

---

**Status icons:** 📋 TODO → 🔄 IN PROGRESS → ✅ DONE → ⏸️ BLOCKED

**Priority:** P0 (must have) → P1 (should have) → P2 (nice to have)
