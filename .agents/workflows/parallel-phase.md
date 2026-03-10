---
description: Chia phase lớn thành streams song song — dùng khi phase có > 8 tasks
---

> Chia phase lớn thành streams song song — dùng khi phase có > 8 tasks.
> Nếu phase nhỏ (≤ 5 tasks, 1 domain) → dùng `/dev` workflow thay thế.

## 1. Analyze Phase Scope

- Đọc `docs/PROJECT_CONTEXT.md` → hiểu current status
- Liệt kê TẤT CẢ features/tasks cần làm
- Ước lượng tổng tasks → nếu > 8 → tiếp tục workflow này

## 2. Chia Streams

Nhóm tasks theo **domain/concern**:

| Stream type  | Ví dụ                          |
| ------------ | ------------------------------ |
| **Bot**      | Handlers, validators, services |
| **Mini App** | React components, pages        |
| **DB**       | Schema, migrations, queries    |
| **Infra**    | Vercel config, GitHub Actions  |

**Nguyên tắc:** Mỗi stream 3-8 tasks, tối thiểu file overlap.

## 3. Tạo TASK_BOARD.md

**Status icons:** 📋 TODO → 🔄 IN PROGRESS → ✅ DONE → ⏸️ BLOCKED

## 4. Execute

1. Đọc PROJECT_CONTEXT trước
2. Đọc TASK_BOARD → hiểu scope + dependencies
3. Update status khi hoàn thành task
4. Test + verify sau mỗi nhóm tasks

## 5. Finalize

1. Verify syntax/build check
2. Update docs — PROJECT_CONTEXT
3. Chạy `/task-completion`
