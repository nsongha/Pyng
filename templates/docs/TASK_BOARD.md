# [Phase Name] Task Board — [Tên Phase] (v[X.Y.Z])

> 🎯 Mục tiêu: [mô tả mục tiêu phase]
> Version target: v[X.Y.Z]

## Thuật ngữ

- **Stream**: Nhóm tasks theo domain/concern — mỗi stream chạy trong 1 conversation riêng
- **Wave**: Đợt chạy, gộp 1+ streams cùng execution order (sequential trước, parallel sau)

## Parallel Execution Strategy

Phase này có [N] tasks chia [M] streams, [W] waves:

| Stream            | Domain   | Scope       | Wave |
| ----------------- | -------- | ----------- | ---- |
| [Emoji] **[Tên]** | [domain] | `[folders]` | 1    |
| [Emoji] **[Tên]** | [domain] | `[folders]` | 2    |
| [Emoji] **[Tên]** | [domain] | `[folders]` | 2    |

**Execution order**: [Stream X] (Wave 1) → [Stream Y] + [Stream Z] (Wave 2, song song)

---

## Context: Codebase Hiện Tại

### Tech Stack

- **Backend**: [tech + version]
- **Frontend**: [tech + version]
- **Testing**: [framework + version]
- **Version hiện tại**: [X.Y.Z]

### Foundation Available

<!-- Liệt kê các files/modules có sẵn mà streams sẽ dựa vào -->

- `[file/module]` — [mô tả]
- `[file/module]` — [mô tả]

### API Endpoints Available

| Method | Path       | Mô tả   |
| ------ | ---------- | ------- |
| GET    | `/api/...` | [mô tả] |

---

## Stream [Emoji] A — [Tên Stream]

**Owner**: [domain]
**Scope**: [folders affected]

| #   | Task        | Status | Priority | Dependencies | Files affected |
| --- | ----------- | ------ | -------- | ------------ | -------------- |
| A1  | [Task name] | 📋     | P0       | —            | `[files]`      |
| A2  | [Task name] | 📋     | P0       | A1           | `[files]`      |
| A3  | [Task name] | 📋     | P1       | A1, A2       | `[files]`      |

**Acceptance Criteria:**

- A1: [Tiêu chí cụ thể]
- A2: [Tiêu chí cụ thể]
- A3: [Tiêu chí cụ thể]

---

## Stream [Emoji] B — [Tên Stream]

**Owner**: [domain]
**Scope**: [folders affected]

| #   | Task        | Status | Priority | Dependencies | Files affected |
| --- | ----------- | ------ | -------- | ------------ | -------------- |
| B1  | [Task name] | 📋     | P0       | —            | `[files]`      |
| B2  | [Task name] | 📋     | P0       | —            | `[files]`      |

**Acceptance Criteria:**

- B1: [Tiêu chí cụ thể]
- B2: [Tiêu chí cụ thể]

---

## Cross-Stream Dependencies

### Dependency Map

| Task | Depends on | Type         | Notes                             |
| ---- | ---------- | ------------ | --------------------------------- |
| A2   | A1         | in-stream    | [lý do]                           |
| B1   | A3         | cross-stream | [lý do — cần module gì từ A3]     |
| B3   | A4, A5     | cross-stream | [lý do — cần service + validator] |

### Execution Order

1. **Wave 1** (Sequential ⛓️): Stream A — foundation, phải xong trước
2. **Wave 2** (Parallel 🔀): Stream B + Stream C — independent, chạy song song

---

## Conflict Prevention Rules

### Shared Files

| File              | Streams dùng  | Tasks  | Rule                                      |
| ----------------- | ------------- | ------ | ----------------------------------------- |
| `[shared file 1]` | [Stream A, B] | A1, B3 | [ai sửa trước, ai chỉ đọc, quy tắc merge] |
| `[shared file 2]` | [Stream B, C] | B1, C2 | [quy tắc cụ thể]                          |

### Merge Strategy

- Mỗi stream KHÔNG commit riêng — gộp commit ở bước Finalize
- Nếu 2 streams cùng cần sửa 1 file → stream chạy SAU phải đọc lại file trước khi sửa
- Sync point: sau mỗi wave hoàn thành → verify trước khi bắt đầu wave tiếp

---

## Progress Summary

| Stream  | Total   | Done  | Remaining | %      |
| ------- | ------- | ----- | --------- | ------ |
| A       | [N]     | 0     | [N]       | 0%     |
| B       | [N]     | 0     | [N]       | 0%     |
| **All** | **[N]** | **0** | **[N]**   | **0%** |

---

## Execution Playbook

### Wave 1 — [Tên] (Sequential ⛓️)

> Stream(s) phải chạy TRƯỚC vì các stream sau depend on nó.

**Streams**: [list]
**Chạy**: Tuần tự, 1 chat

#### Prompt — Stream [X]:

```
Triển khai Stream [X] ([tên]) trong @TASK_BOARD.md
Đọc section "Context: Codebase Hiện Tại" để hiểu foundation.
Đọc "Conflict Prevention Rules" → chỉ sửa files trong scope.
Làm từ task P0 trước (X1 → X2 → ...), sau đó P1.
```

**✅ Sau khi Wave 1 xong**:

1. Kiểm tra TASK_BOARD.md → confirm tất cả tasks Wave 1 = ✅
2. Verify: `python3 -m py_compile [files]`
3. Bắt đầu Wave 2

---

### Wave 2 — [Tên] (Parallel 🔀)

> Các streams này KHÔNG depend nhau → chạy SONG SONG trong chat riêng.

**Streams**: [list]
**Chạy**: Mỗi stream 1 chat riêng, chạy cùng lúc

#### Prompt — Stream [Y] (Chat 1):

```
Triển khai Stream [Y] ([tên]) trong @TASK_BOARD.md
Stream [X] đã hoàn thành (Wave 1). Đọc section "Context" + code mới.
Đọc "Conflict Prevention Rules" → chỉ sửa files trong scope.
Làm từ task P0 trước (Y1 → Y2 → ...), sau đó P1, cuối cùng P2.
```

#### Prompt — Stream [Z] (Chat 2):

```
Triển khai Stream [Z] ([tên]) trong @TASK_BOARD.md
Stream [X] đã hoàn thành (Wave 1). Đọc section "Context" + code mới.
Đọc "Conflict Prevention Rules" → chỉ sửa files trong scope.
Làm task Z1 → Z2 → Z3.
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
Tất cả streams Phase [N] đã xong. Chạy bước 6-7 của /parallel-phase:
- Verify build (py_compile tất cả files)
- Confirm TASK_BOARD.md 100%
- Chạy /code-review trên toàn bộ thay đổi phase
- Finalize: gộp changelog, update PROJECT_CONTEXT.md + DEV_ROADMAP.md, commit
```

---

**Status icons:** 📋 TODO → 🔄 IN PROGRESS → ✅ DONE → ⏸️ BLOCKED

**Priority:** P0 (must have) → P1 (should have) → P2 (nice to have)
