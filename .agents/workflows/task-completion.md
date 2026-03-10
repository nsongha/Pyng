---
description: Workflow chạy sau khi hoàn thành task — verify build, update docs, commit
---

> Chạy sau khi hoàn thành mỗi task — verify, review, commit.

## 1. Verification (`verification-before-completion`)

> ⚠️ BẮT BUỘC trước khi claim "done". Invoke skill `verification-before-completion`.

- Chạy actual test/build command và **xác nhận output thành công**
- Không chỉ "assume" mọi thứ ổn — phải thấy output pass

```bash
# Python: kiểm tra syntax
python -m py_compile <file.py>

# Mini App: build check
cd miniapp && npm run build

# Bot: test import
python -c "from bot.handlers import checkin; print('OK')"
```

## 2. Code Review (`/code-review`)

- Chạy checklist `/code-review` — đảm bảo pass hết items

## 3. Cập nhật docs nếu cần

- `docs/PROJECT_CONTEXT.md` — nếu thay đổi kiến trúc/scope
- `CHANGELOG.md` — thêm entry vào `[Unreleased]`
- `docs/KNOWN_ISSUES.md` — nếu phát hiện bug mới hoặc resolve bug cũ

## 4. Git add và commit

```bash
git add -A
git status
```

## 5. Commit với Conventional Commits (tiếng Việt)

```bash
git commit -m "<type>: <mô tả ngắn bằng tiếng Việt>"
```

| Type        | Mô tả                        |
| ----------- | ---------------------------- |
| `feat:`     | Tính năng mới                |
| `fix:`      | Bug fix                      |
| `docs:`     | Chỉ thay đổi tài liệu        |
| `refactor:` | Refactor, không đổi behavior |
| `chore:`    | Build, config                |
