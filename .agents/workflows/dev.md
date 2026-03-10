---
description: Workflow phát triển feature mới
---

> Workflow phát triển feature mới — tích hợp skills theo từng bước.

## 1. Đọc context

- Đọc `docs/PROJECT_CONTEXT.md` trước tiên
- Đọc `docs/ARCHITECTURE.md` nếu liên quan đến DB/API
- Đọc `docs/BOT_FLOWS.md` nếu liên quan đến conversation flow

## 2. Phân tích yêu cầu

- Feature này thay đổi **Bot** (handlers), **Mini App** (React), hay cả hai?
- Có ảnh hưởng tới DB schema không? → đọc `docs/ARCHITECTURE.md` §2
- Cần thêm API endpoint mới không? → invoke skill `api-design-principles`
- Feature phức tạp (> 3 modules)? → invoke skill `architecture-patterns`

## 3. Plan theo skill phù hợp

| Scope thay đổi        | Skill cần đọc trước khi code                            |
| --------------------- | ------------------------------------------------------- |
| Bot handler/validator | `telegram-bot-builder`                                  |
| Mini App (TWA)        | `telegram-mini-app`                                     |
| API endpoint mới      | `api-design-principles` + `api-security-best-practices` |
| DB query/schema       | `postgres-best-practices`                               |
| Async logic           | `async-python-patterns`                                 |

Nếu phức tạp (> 3 files): viết implementation plan trước.

## 4. Implement — follow skills

- **Python code:** follow `python-pro` (type hints, modern syntax, clean structure)
- **Async handlers:** follow `async-python-patterns` (async/await, error handling)
- **FastAPI endpoints:** follow `python-fastapi-development` + `pydantic-models-py`
- **DB queries:** follow `postgres-best-practices` (indexes, parameterized queries)
- **Supabase calls:** follow `supabase-automation` (RLS, correct client usage)
- **React components:** follow `react-best-practices` (performance, hooks)
- **Tailwind styling:** follow `tailwind-patterns` (design tokens, responsive)

## 5. Test

- Invoke skill `test-driven-development` — viết test trước nếu logic phức tạp
- Chạy bot (polling mode) và test trên Telegram
- Test edge cases — xem `docs/KNOWN_ISSUES.md`

## 6. Hoàn tất

- Chạy `/code-review` checklist
- Chạy `/task-completion`
