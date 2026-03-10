# [Phase Name] Task Board — [Tên Phase] (v[X.Y.Z])

> 🎯 Mục tiêu: [mô tả mục tiêu phase]
> Version target: v[X.Y.Z]

## Parallel Execution Strategy

Phase này có [N] tasks chia [M] streams theo domain:

- **Stream A — [Tên]**: [Mô tả scope] ([domain])
- **Stream B — [Tên]**: [Mô tả scope] ([domain])
- **Stream C — [Tên]**: [Mô tả scope] ([domain])

[Ghi chú về dependencies giữa streams]

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

| Task | Depends on | Type         | Notes   |
| ---- | ---------- | ------------ | ------- |
| A2   | A1         | in-stream    | [lý do] |
| B3   | A3         | cross-stream | [lý do] |

### Execution Order

- **Stream A** và **Stream B** [independent / sequential]
- **Stream C** phụ thuộc vào [conditions]

## Conflict Prevention Rules

### Shared Files

| File            | Stream A | Stream B | Rule                     |
| --------------- | -------- | -------- | ------------------------ |
| `[shared file]` | [tasks]  | [tasks]  | [quy tắc tránh conflict] |

### Merge Strategy

- Stream A: [strategy]
- Stream B: [strategy]
- Sync point: [khi nào sync]

## Progress Summary

| Stream  | Total   | Done  | Remaining | %      |
| ------- | ------- | ----- | --------- | ------ |
| A       | [N]     | 0     | [N]       | 0%     |
| B       | [N]     | 0     | [N]       | 0%     |
| **All** | **[N]** | **0** | **[N]**   | **0%** |

---

**Status icons:** 📋 TODO → 🔄 IN PROGRESS → ✅ DONE → ⏸️ BLOCKED

**Priority:** P0 (must have) → P1 (should have) → P2 (nice to have)
