---
description: Checklist review code tự động trước khi commit
---

> Checklist review code trước khi commit — dựa trên skills đã cài.

## 1. Python Code Quality (`python-pro`)

- [ ] Type hints đầy đủ cho function params và return
- [ ] Không có `print()` debug còn sót — dùng `logging` module
- [ ] Functions < 50 lines, single responsibility
- [ ] Naming rõ ràng: snake_case cho functions/variables
- [ ] Không hardcoded values (paths, URLs, credentials)

## 2. Async Patterns (`async-python-patterns`)

- [ ] Dùng `async/await` đúng cách — không block event loop
- [ ] `asyncio.sleep()` thay `time.sleep()` trong async context
- [ ] Error handling: `try/except` bao quanh external calls (Telegram API, Supabase)
- [ ] Timeout cho mọi external call

## 3. API & Security (`api-security-best-practices`)

- [ ] Không có secrets/keys trong code — dùng env vars
- [ ] Input validation cho mọi API endpoint (`pydantic-models-py`)
- [ ] CORS config chỉ allow origins cần thiết
- [ ] JWT validation cho Mini App API
- [ ] SQL injection protection — parameterized queries only

## 4. Database (`postgres-best-practices`)

- [ ] Không có N+1 queries
- [ ] Index cho columns thường query (user_id, checked_at)
- [ ] Supabase RLS enabled cho tables mới
- [ ] Migration SQL tested trên Supabase SQL Editor

## 5. Frontend — Mini App (`react-best-practices` + `tailwind-patterns`)

- [ ] Components không quá lớn — tách nhỏ nếu > 100 lines
- [ ] Hooks đúng rules (không gọi conditional, không trong loop)
- [ ] Tailwind classes consistent với design tokens Pyng (`--pyng-red`, `--pyng-dark`)
- [ ] Responsive trên mobile (Telegram Mini App chủ yếu dùng trên mobile)

## 6. Docs

- [ ] CHANGELOG.md cập nhật nếu có feature/fix mới
- [ ] PROJECT_CONTEXT.md cập nhật nếu thay đổi kiến trúc
- [ ] KNOWN_ISSUES.md cập nhật nếu phát hiện/resolve bug
