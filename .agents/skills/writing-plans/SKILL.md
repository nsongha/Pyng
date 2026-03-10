---
name: writing-plans
description: Viết implementation plan chi tiết với bite-sized tasks, exact file paths, và commands. Dùng trước khi bắt đầu implement feature hoặc phase.
---

# Writing Plans

## Overview

Viết implementation plan giả định người execute có **zero context** về codebase. Mọi thứ phải rõ ràng: file nào, code gì, command nào, expect output gì.

**Dùng khi:**

- Bắt đầu Phase mới trong DEV_ROADMAP
- Feature phức tạp (> 3 files thay đổi)
- User yêu cầu plan trước khi code

## Quy trình

### 1. Đọc context

- `docs/PROJECT_CONTEXT.md` → hiểu project
- `docs/DEV_ROADMAP.md` → scope phase hiện tại
- `docs/ARCHITECTURE.md` → kiến trúc hiện tại
- `docs/BOT_FLOWS.md` → conversation flows (nếu thêm command)

### 2. Scope Check

Nếu scope quá lớn (> 10 tasks / > 2 domains):

- Đề xuất tách thành sub-plans
- Mỗi sub-plan tạo phần mềm hoạt động độc lập
- → Dùng `/parallel-phase` thay thế

### 3. File Structure

Trước khi viết tasks, map ra:

- Files nào cần tạo mới
- Files nào cần sửa
- Thứ tự: database → services → handlers → tests

### 4. Bite-Sized Tasks

**Mỗi step là 1 action (2-5 phút):**

````markdown
### Task 1: Tạo Service kiểm tra GPS

**Files:**

- Tạo: `services/location.py`
- Sửa: `bot/handlers/checkin.py`
- Test: `tests/test_location.py`

- [ ] **Step 1: Tạo function validate_location**

```python
def validate_location(lat: float, lng: float, office_lat: float, office_lng: float, radius: int) -> bool:
    """Kiểm tra vị trí nằm trong geofence."""
    from geopy.distance import geodesic
    distance = geodesic((lat, lng), (office_lat, office_lng)).meters
    return distance <= radius
```
````

- [ ] **Step 2: Verify syntax**

```bash
python3 -m py_compile services/location.py
```

- [ ] **Step 3: Commit**

```bash
git add services/location.py
git commit -m "feat: thêm validate_location service"
```

````

### 5. Plan Document Header

```markdown
# [Feature Name] Implementation Plan

**Goal:** [Mô tả 1 dòng]
**Architecture:** [2-3 câu về approach]
**Files affected:** [Danh sách files]

---
````

## Rules

- **Exact file paths** — luôn ghi đường dẫn đầy đủ
- **Code đầy đủ** — không viết "thêm validation", viết code thực
- **Commands cụ thể** — ghi exact command + expected output
- **DRY, YAGNI** — không thêm gì chưa cần
- **Frequent commits** — mỗi task = 1 commit

## Không conflict với workflows

- Plan nhỏ (≤ 5 tasks) → execute bằng `/new-feature`
- Plan lớn (> 8 tasks) → execute bằng `/parallel-phase`
- Plan trung bình (6-8 tasks) → chia 2-3 chats sequential
