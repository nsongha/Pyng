---
description: Quy trình chia phase lớn thành streams song song, tạo task board, execute multi-conversation
---

# Parallel Phase Execution

> Dùng khi phase có **> 8 tasks** hoặc **chạm > 2 domains** (bot + api + miniapp).
> Nếu phase nhỏ (≤ 5 tasks, 1 domain) → dùng `/new-feature` thay thế.

## 1. Analyze Phase Scope

- Đọc `docs/PROJECT_CONTEXT.md` → hiểu current status
- Đọc `docs/DEV_ROADMAP.md` → xem scope phase cần triển khai
- Liệt kê TẤT CẢ features/tasks cần làm
- Ước lượng tổng tasks → nếu > 8 → tiếp tục workflow này

## 2. Chia Streams

Nhóm tasks theo **domain/concern**, KHÔNG theo thứ tự thời gian:

| Stream type      | Ví dụ                         | Khi nào dùng                   |
| ---------------- | ----------------------------- | ------------------------------ |
| **Bot Handlers** | Commands, conversation flows  | Có thay đổi `bot/handlers/`    |
| **Services**     | Business logic, DB queries    | Có thay đổi `services/`        |
| **API**          | Webhook, cron endpoints       | Có thay đổi `api/`             |
| **Mini App**     | React components, pages       | Có thay đổi `miniapp/`         |
| **Database**     | Schema, migrations, seed data | Có thay đổi `db/`, `supabase/` |
| **Infra/Config** | Vercel, GitHub Actions, env   | Có thay đổi deploy/config      |

**Nguyên tắc chia:**

- Mỗi stream 3-8 tasks (không quá ít, không quá nhiều)
- Tối thiểu file overlap giữa streams
- Xác định shared files → ghi rõ ai sửa trước
- Nếu 1 stream quá lớn → tách thành 2

## 3. Tạo TASK_BOARD.md

Tạo file `docs/TASK_BOARD.md` với cấu trúc sau:

```markdown
# Phase X Task Board

## Parallel Execution Strategy

- Tổng quan streams, mục tiêu, timeline

## Context: Codebase Hiện Tại

> Section này giúp AI agent hiểu codebase mà KHÔNG cần đọc toàn bộ history.

- Tech stack liên quan
- Files/modules đã có sẵn (foundation)
- API endpoints available

## Stream [Emoji] [Tên]

**Owner**: [domain]
**Scope**: [folders affected]

| #   | Task | Status | Priority | Dependencies | Files affected |
| --- | ---- | ------ | -------- | ------------ | -------------- |
| X1  | ...  | 📋     | P0       | -            | ...            |

**Acceptance Criteria per task:**

- Tiêu chí cụ thể để đánh giá task hoàn thành

## Cross-Stream Dependencies

| Task | Depends on | Type         |
| ---- | ---------- | ------------ |
| C3   | B3 ✅      | cross-stream |

## Progress Summary

| Stream | Total | Done | Remaining | % |
```

**Status icons:** 📋 TODO → 🔄 IN PROGRESS → ✅ DONE → ⏸️ BLOCKED

**Priority:** P0 (must have) → P1 (should have) → P2 (nice to have)

## 4. Review & Approve Task Board

- Trình task board cho user review
- Điều chỉnh streams/tasks nếu cần
- Xác nhận execution order

## 5. Execute — Multi-Conversation

### Prompt template cho mỗi stream:

```
Triển khai Stream [X] ([tên]) trong @TASK_BOARD.md
Làm từ task có priority P0 trước, skip task nào bị BLOCKED.
```

### Nối tiếp stream (conversation mới):

```
Tiếp tục Stream [X] trong @TASK_BOARD.md — các task X1, X2 đã xong, tiếp từ X3.
```

### Rules cho AI agent trong mỗi stream:

1. **Đọc `PROJECT_CONTEXT.md` trước** (user rules đã bắt buộc)
2. **Đọc `TASK_BOARD.md`** → hiểu scope + dependencies + context
3. **Check Cross-Stream Dependencies** trước khi bắt đầu task
4. **Update status** trên TASK_BOARD.md khi hoàn thành task (📋 → ✅) + update Progress Summary
5. **Chỉ sửa files trong scope** của stream mình
6. **Test + verify** sau mỗi nhóm tasks (bước 1-2 của `/task-completion`)
7. **KHÔNG tự commit** — commit sẽ được gộp ở bước merge

### Lưu ý song song:

- Mỗi stream chạy trong **1 chat riêng** → context sạch
- Agent **TỰ update** TASK_BOARD.md status — user không cần canh
- **KHÔNG chạy bước 3-4-5** của `/task-completion` (commit, docs update) → dồn vào bước merge

## 6. Verify & Review

Sau khi tất cả streams hoàn thành, mở 1 chat mới:

```
Tất cả streams Phase [X] đã xong. Chạy bước 6-7 của /parallel-phase:
- Verify build
- Confirm TASK_BOARD.md 100%
- Chạy /code-review trên toàn bộ thay đổi phase
- Finalize: gộp changelog, update docs, commit
```

### Checklist verify:

// turbo

1. `python3 -m py_compile` trên tất cả files thay đổi

// turbo

2. `vercel --prod --yes` — deploy thành công

3. Test trên Telegram — verify bot commands hoạt động
4. Review TASK_BOARD.md → confirm 100%
5. Chạy `/code-review` trên toàn bộ diff của phase → fix P0/P1

## 7. Finalize

1. **Gộp changelog** — nhiều stream entries → 1 version entry
2. **Update docs** — `PROJECT_CONTEXT.md`, `DEV_ROADMAP.md`
3. **Commit** — 1 commit gọn: `docs: ...`
4. **Chạy `/task-completion`** cho commit code (nếu chưa commit từng stream)

## LƯU Ý QUAN TRỌNG

- Phase **≤ 5 tasks** → KHÔNG dùng workflow này, dùng `/new-feature`
- Phase **6-10 tasks** → optional, có thể chia 2-3 chats đơn giản
- Phase **> 10 tasks** → BẮT BUỘC dùng workflow này
- Khi chia streams, ưu tiên **ít file overlap** hơn là cân bằng số tasks
- Progress Summary luôn phải được AI agent cập nhật → user chỉ cần nhìn bảng tổng
