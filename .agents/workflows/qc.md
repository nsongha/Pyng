---
description: QC test plan và verification — kiểm tra code CHẠY ĐÚNG không (scenarios, edge cases, regression)
---

# /qc — Quality Control

> **Phân vùng trách nhiệm:**
>
> - `/task-completion` → Code **chạy được** không? (syntax, import, deploy)
> - `/code-review` → Code **viết tốt** không? (security, quality, naming)
> - `/qc` → Code **chạy đúng** không? (scenarios, edge cases, regression)

## Khi nào dùng

| Tình huống                                          | Mode     |
| --------------------------------------------------- | -------- |
| Planning phase mới (`/parallel-phase` bước 3)       | `--plan` |
| Sau khi implement xong, trước `/code-review`        | `--run`  |
| Feature phức tạp trong `/new-feature` (≥ 3 modules) | `--run`  |
| Bất kỳ lúc nào muốn verify behavior                 | `--run`  |

---

## Mode 1: `--plan` (Tạo QC Test Plan)

> Chạy khi planning, TRƯỚC khi implement.

### 1. Xác định scope

- Đọc `docs/DEV_ROADMAP.md` → features cần implement
- Đọc `docs/TASK_BOARD.md` → streams và tasks cụ thể (nếu có)
- Đọc `docs/PROJECT_CONTEXT.md` → hiểu modules hiện có

### 2. Tạo test cases cho mỗi feature/stream

Với mỗi feature, tạo **3-5 test cases** theo format:

```
TC-{module}-{số}: {Mô tả scenario}
  → Input: {mô tả input}
  → Expected: {kết quả mong đợi}
  → Type: happy | edge | error
```

**Phân loại bắt buộc:**

| Type      | Số lượng tối thiểu | Ví dụ                                        |
| --------- | ------------------ | -------------------------------------------- |
| Happy     | 1-2 per feature    | GPS check-in trong bán kính 50m → thành công |
| Edge case | 1-2 per feature    | GPS check-in đúng 120m → border case         |
| Error     | 1 per feature      | GPS check-in cách 200m → bị từ chối          |

### 3. Tạo regression test cases

- Liệt kê features CŨ có thể bị ảnh hưởng bởi code mới
- Tạo 1-2 regression TCs cho mỗi feature cũ bị ảnh hưởng
- Format: `TC-REG-{số}: {feature cũ} vẫn hoạt động sau khi {thay đổi mới}`

### 4. Output

Ghi test cases vào 1 trong 2 nơi:

- **Nếu đang dùng `/parallel-phase`** → thêm section "## QC Test Plan" trong `docs/TASK_BOARD.md`
- **Nếu standalone** → tạo/update `docs/QC_REPORT.md` section "Test Cases" (theo template `templates/docs/QC_REPORT.md`)

---

## Mode 2: `--run` (Chạy QC + Report)

> Chạy SAU khi implement, TRƯỚC `/code-review`.

### 1. Đọc test plan

- Tìm test cases trong `docs/TASK_BOARD.md` (section QC Test Plan)
- Hoặc `docs/QC_REPORT.md` (nếu đã có)
- Nếu CHƯA có test plan → tự tạo nhanh theo Mode 1

### 2. Chạy từng test case

Với mỗi TC, verify bằng phương pháp phù hợp (ưu tiên từ trên xuống):

| Phương pháp         | Khi nào dùng                  | Ví dụ                                              |
| ------------------- | ----------------------------- | -------------------------------------------------- |
| **Import test**     | Verify module load thành công | `python3 -c "from services.qr_service import ..."` |
| **Code path trace** | Verify logic flow đúng        | Đọc code, trace từ input → output                  |
| **curl endpoint**   | Verify API response           | `curl -s https://pyng.vercel.app/api/qr/current`   |
| **Schema check**    | Verify DB query đúng          | Check parameterized query, column names            |

// turbo

```bash
# Ví dụ import test cho tất cả modules
python3 -c "
from bot.app import create_bot
from services.user_service import register_user, activate_user
from services.checkin_service import checkin, checkout
from services.office_service import get_office, get_wifi_whitelist
print('✅ All modules import OK')
"
```

### 3. Ghi kết quả

Với mỗi TC:

- `[x]` = pass — ghi evidence ngắn gọn
- `[ ]` = fail — ghi actual result + root cause

### 4. Regression check

- Chạy regression TCs (nếu có trong plan)
- Nếu KHÔNG có plan → verify import + basic logic của modules KHÔNG thay đổi nhưng bị depend

### 5. Output: `docs/QC_REPORT.md`

Tạo/update `docs/QC_REPORT.md` theo template `templates/docs/QC_REPORT.md`:

```markdown
# QC Report — Pyng

> Cập nhật: YYYY-MM-DD
> Version: vX.Y.Z · Branch: main

## Test Cases

### [Feature 1]

- [x] TC-GPS-01: Check-in trong bán kính → thành công ✅
- [x] TC-GPS-02: Check-in ngoài bán kính → từ chối ✅
- [ ] TC-GPS-03: Spoofing detection → ❌ chưa handle edge case

### Regression

- [x] TC-REG-01: WiFi check-in vẫn OK sau thay đổi GPS module ✅

## Summary

- Total: N test cases
- Pass: N ✅
- Fail: N ❌
- Block release: Có/Không
```

### 6. Action dựa trên kết quả

| Kết quả              | Action                                          |
| -------------------- | ----------------------------------------------- |
| 100% pass            | ✅ Proceed to `/code-review`                    |
| Có fail non-critical | ⚠️ Ghi vào `KNOWN_ISSUES.md`, proceed with note |
| Có fail critical     | 🛑 DỪNG — fix ngay, chạy lại `/qc --run`        |

**Critical = feature chính không hoạt động hoặc data corruption risk**

---

## LƯU Ý

- `/qc --plan` và `--run` là **2 bước riêng**, không nhất thiết chạy cùng lúc
- Test cases nên **cụ thể, measurable** — tránh "verify hoạt động đúng" chung chung
- Regression TCs **tích lũy** qua các phases — phase sau thêm TCs mới, giữ TCs cũ
- QC_REPORT.md là **living document** — update qua mỗi phase, không xóa results cũ
- Nếu feature quá đơn giản (1 handler, no deps) → KHÔNG cần `/qc`, bước 7 của `/new-feature` đủ
