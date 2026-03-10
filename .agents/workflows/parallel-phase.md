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

### ⚠️ BẮT BUỘC: Trình Execution Playbook trong chat

Khi trình task board, AI **PHẢI ghi trực tiếp trong message** (không chỉ trong file):

1. **Waves & thứ tự** — wave nào chạy trước, wave nào song song
2. **Prompts copy-paste** cho từng stream — user copy dán vào chat mới là chạy được
3. **Sau mỗi wave làm gì** — verify gì, rồi chuyển wave tiếp thế nào
4. **Sau khi TẤT CẢ xong** — prompt verify & finalize

User KHÔNG cần mở TASK_BOARD.md mới biết phải làm gì tiếp.

## 5. Execute — Multi-Conversation

### 5.1 Viết Execution Playbook trong TASK_BOARD.md

Sau khi tạo task board, **BẮT BUỘC** thêm section `## Execution Playbook` vào cuối TASK_BOARD.md với:

```markdown
## Execution Playbook

### Wave 1 — [tên] (Sequential ⛓️)

> Streams phải chạy TRƯỚC vì các stream sau depend on nó.

**Streams**: [list]
**Chạy**: Tuần tự, 1 chat

#### Prompt — Stream [X]:

> Triển khai Stream [X] ([tên]) trong @TASK_BOARD.md
> Đọc section "Context: Codebase Hiện Tại" để hiểu foundation.
> Làm từ task P0 trước, skip task BLOCKED.

**✅ Sau khi Wave 1 xong**: Kiểm tra TASK_BOARD.md → confirm tất cả tasks Wave 1 = ✅, rồi bắt đầu Wave 2.

---

### Wave 2 — [tên] (Parallel 🔀)

> Các streams này KHÔNG depend nhau → chạy SONG SONG.

**Streams**: [list]
**Chạy**: Mỗi stream 1 chat riêng, chạy cùng lúc

#### Prompt — Stream [Y] (Chat 1):

> Triển khai Stream [Y] ([tên]) trong @TASK_BOARD.md
> Stream [X] đã hoàn thành (Wave 1). Đọc section "Context" + stream [X] để hiểu code mới.
> Làm từ task P0 trước.

#### Prompt — Stream [Z] (Chat 2):

> Triển khai Stream [Z] ([tên]) trong @TASK_BOARD.md
> Stream [X] đã hoàn thành (Wave 1). Đọc section "Context" + stream [X] để hiểu code mới.
> Làm từ task P0 trước.

**✅ Sau khi Wave 2 xong**: Cả 2 chat đều xong → mở chat mới chạy bước 6 (Verify & Review).

---

### Nối tiếp stream (nếu 1 chat bị ngắt):

> Tiếp tục Stream [X] trong @TASK_BOARD.md — các task X1, X2 đã xong (✅), tiếp từ X3.

### Sau khi TẤT CẢ waves xong:

> Tất cả streams Phase [N] đã xong. Chạy bước 6-7 của /parallel-phase:
>
> - Verify build
> - Confirm TASK_BOARD.md 100%
> - Chạy /code-review trên toàn bộ thay đổi phase
> - Finalize: gộp changelog, update docs, commit
```

### 5.2 Nguyên tắc chia Waves

| Điều kiện                                    | Wave type                                   |
| -------------------------------------------- | ------------------------------------------- |
| Stream **là dependency** của streams khác    | Wave sớm, **Sequential ⛓️**                 |
| Stream **không depend** stream nào cùng wave | **Parallel 🔀** — chạy song song            |
| Stream phụ thuộc stream cùng wave            | Gộp chung wave, chạy **tuần tự trong wave** |

### 5.3 Rules cho AI agent trong mỗi stream

1. **Đọc `PROJECT_CONTEXT.md` trước** (user rules đã bắt buộc)
2. **Đọc `TASK_BOARD.md`** → hiểu scope + dependencies + context + execution playbook
3. **Check Cross-Stream Dependencies** trước khi bắt đầu task
4. **Update status** trên TASK_BOARD.md khi hoàn thành task (📋 → ✅) + update Progress Summary
5. **Chỉ sửa files trong scope** của stream mình
6. **Test + verify** sau mỗi nhóm tasks (bước 1-2 của `/task-completion`)
7. **KHÔNG tự commit** — commit sẽ được gộp ở bước merge

### 5.4 Lưu ý song song

- Mỗi stream chạy trong **1 chat riêng** → context sạch
- Agent **TỰ update** TASK_BOARD.md status — user không cần canh
- **KHÔNG chạy bước 3-4-5** của `/task-completion` (commit, docs update) → dồn vào bước merge
- Nếu 2 streams cùng wave sửa **shared file** → ghi rõ trong playbook ai sửa trước

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
