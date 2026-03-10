---
description: Testing guidelines, khi nào đề xuất test, verification trước commit
---

# Testing

## Khi nào đề xuất test

- Logic phức tạp (nhiều branch, edge cases) → đề xuất unit test
- Service function có nhiều input variations → gợi ý test cases
- CRUD đơn giản, handler đơn giản → KHÔNG cần nhắc test

> Lưu ý: Chỉ **đề xuất**, không tự viết test trừ khi user yêu cầu.

## Test Cases

- Gợi ý bao gồm: happy path, edge cases, error cases
- Ưu tiên test behavior (output), không test implementation
- Mock external services: Telegram API, Supabase, GPS

## Pre-commit Verification

- Verify syntax: `python3 -m py_compile <files>`
- Test imports: `python3 -c "from bot.app import create_bot"`
- Verify deploy: `vercel --prod --yes`
- Không commit code có failing tests hoặc syntax errors

## Test Tools

- `pytest` cho unit tests
- `pytest-asyncio` cho async functions
- `unittest.mock` cho mocking
- `httpx` cho HTTP client testing
