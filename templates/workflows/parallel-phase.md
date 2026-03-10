---
description: Quy trình chia phase lớn thành streams song song, tạo task board, execute multi-conversation
---

# Parallel Phase Execution

> Dùng khi phase có **> 8 tasks** hoặc **chạm > 2 apps** (api + web + mobile).
> Nếu phase nhỏ (≤ 5 tasks, 1 domain) → dùng `/new-feature` thay thế.

## 1. Analyze Phase Scope

- Đọc `docs/AI_CONTEXT.md` → hiểu current status
- Đọc `docs/APP_DESCRIPTION.md` → xem scope phase cần triển khai
- Liệt kê TẤT CẢ features/tasks cần làm
- Ước lượng tổng tasks → nếu > 8 → tiếp tục workflow này

## 2. Chia Streams

Nhóm tasks theo **domain/concern**, KHÔNG theo thứ tự thời gian:

| Stream type      | Ví dụ                                      | Khi nào dùng               |
| ---------------- | ------------------------------------------ | -------------------------- |
| **Backend**      | API endpoints, Prisma schema               | Có thay đổi `apps/api/`    |
| **Frontend Web** | Pages, components                          | Có thay đổi `apps/web/`    |
| **Mobile**       | Screens, hooks, native modules             | Có thay đổi `apps/mobile/` |
| **Testing**      | Unit tests, E2E tests                      | Cần test coverage mới      |
| **Infra/Config** | Docker, CI/CD, env, build config           | Có thay đổi deploy/config  |
| **Performance**  | Caching, optimization                      | Có yêu cầu performance     |
| **UX Polish**    | Error handling, loading states, animations | Có yêu cầu UX              |

**Nguyên tắc chia:**

- Mỗi stream 3-8 tasks (không quá ít, không quá nhiều)
- Tối thiểu file overlap giữa streams
- Xác định shared files (`package.json`, `app.json`, `_layout.tsx`) → ghi rõ ai sửa trước
- Nếu 1 stream quá lớn → tách thành 2 (ví dụ: Testing → Unit + E2E)

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
- Brand colors, conventions

## Stream [Emoji] [Tên]

**Owner**: [domain]
**Scope**: [folders affected]

| #   | Task | Status | Priority | Dependencies | Files affected |
| --- | ---- | ------ | -------- | ------------ | -------------- |
| X1  | ...  | 📋     | P0       | -            | ...            |

**Acceptance Criteria per task:**

- Tiêu chí cụ thể để đánh giá task hoàn thành

## Cross-Stream Dependencies

### Dependency Map

| Task | Depends on | Type         |
| ---- | ---------- | ------------ |
| C3   | B3 ✅      | cross-stream |

### Execution Order

- Week 1: Stream A ←→ Stream B ←→ Stream D-Early
- Week 2: ...

## Conflict Prevention Rules

- Shared files: ai sửa trước?
- Khi merge: sync point ở đâu?

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

1. **Đọc `AI_CONTEXT.md` trước** (user rules đã bắt buộc)
2. **Đọc `TASK_BOARD.md`** → hiểu scope + dependencies + context
3. **Check Cross-Stream Dependencies** trước khi bắt đầu task
4. **Update status** trên TASK_BOARD.md khi hoàn thành task (📋 → ✅) + update Progress Summary
5. **Chỉ sửa files trong scope** của stream mình
6. **Test + verify build** sau mỗi nhóm tasks (bước 1-2 của `/task-completion`)
7. **KHÔNG tự commit** — commit sẽ được gộp ở bước merge

### Lưu ý song song:

- Mỗi stream chạy trong **1 chat riêng** → context sạch
- Agent **TỰ update** TASK_BOARD.md status — user không cần canh
- Nếu 2 streams cùng sửa TASK_BOARD.md → stream sau sẽ tự resolve (file nhỏ, ít conflict)
- **KHÔNG chạy bước 3-4-5** của `/task-completion` (commit, docs update) → dồn vào bước merge

## 6. Verify & Review

Sau khi tất cả streams hoàn thành, mở 1 chat mới:

```
Tất cả streams Phase [X] đã xong. Chạy bước 6-7 của /parallel-phase:
- Verify build (API + Web + Mobile)
- Confirm TASK_BOARD.md 100%
- Chạy /code-review trên toàn bộ thay đổi phase
- Finalize: gộp changelog, update docs, commit
```

### Checklist verify:

// turbo

1. `pnpm build` — verify tất cả apps build thành công

// turbo

2. `pnpm --filter @spamana/api test` — API tests pass

// turbo

3. `pnpm --filter @spamana/mobile test` — Mobile tests pass (nếu có)

4. Resolve conflicts nếu có (shared files)
5. Review TASK_BOARD.md → confirm 100%
6. Chạy `/code-review` trên toàn bộ diff của phase → fix P0/P1 trước khi finalize

> 💡 Bước này KHÔNG phải git merge — tất cả streams đã commit vào cùng branch.
> Mục đích là verify tổng thể + code review cross-stream.

## 7. Finalize

1. **Gộp changelog** — nhiều stream entries → 1 version entry (minor bump)
2. **Update docs** — `AI_CONTEXT.md`, `APP_DESCRIPTION.md`
3. **Commit** — 1 commit gọn: `docs: ...`
4. **Chạy `/task-completion`** cho commit code (nếu chưa commit từng stream)

## LƯU Ý QUAN TRỌNG

- Phase **≤ 5 tasks** → KHÔNG dùng workflow này, dùng `/new-feature`
- Phase **6-10 tasks** → optional, có thể chia 2-3 chats đơn giản
- Phase **> 10 tasks** → BẮT BUỘC dùng workflow này
- Khi chia streams, ưu tiên **ít file overlap** hơn là cân bằng số tasks
- Progress Summary luôn phải được AI agent cập nhật → user chỉ cần nhìn bảng tổng
