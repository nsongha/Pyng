---
description: AI cần đọc context docs trước khi bắt đầu làm việc
---

# AI Context

## Bắt buộc đọc trước khi bắt đầu task

1. `docs/PROJECT_CONTEXT.md` — tổng quan project, tech stack, conventions
2. `docs/DEV_ROADMAP.md` — phase hiện tại, tasks đang làm

## Đọc thêm nếu liên quan

- `docs/ARCHITECTURE.md` — sơ đồ kiến trúc, data flow
- `docs/BOT_FLOWS.md` — conversation flows, command handlers
- `docs/KNOWN_ISSUES.md` — bugs đã biết, workarounds
- `docs/DECISIONS.md` — lý do đằng sau các quyết định kiến trúc
- `docs/TECH_STACK.md` — dependencies, versions, services

## Quy tắc

- KHÔNG bắt đầu code khi chưa đọc context
- KHÔNG assume — nếu thiếu thông tin → hỏi user
- Khi hỏi user, tập trung vào **quyết định cụ thể**, không hỏi chung chung
