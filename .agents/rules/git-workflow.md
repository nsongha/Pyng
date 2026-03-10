---
description: Git workflow, branching, commit conventions
---

# Git Workflow

## Commits

- Conventional Commits format, message bằng **tiếng Việt**
- Mỗi commit = 1 unit of work (không gộp nhiều features)
- Tối đa 2 commits per task: 1 code + 1 docs

| Type        | Mô tả                        |
| ----------- | ---------------------------- |
| `feat:`     | Tính năng mới                |
| `fix:`      | Bug fix                      |
| `refactor:` | Refactor, không đổi behavior |
| `docs:`     | Chỉ thay đổi tài liệu        |
| `chore:`    | Build, config, tooling       |

### Commit Body — BẮT BUỘC khi:

- Commit ≥ 3 files thay đổi
- Commit type là `feat:` hoặc `chore:`
- Có nhiều thay đổi đáng chú ý

**Format body:**

```
<type>: <mô tả ngắn tiếng Việt>

- Bullet point 1: mô tả thay đổi cụ thể
- Bullet point 2: file/module gì thay đổi
- Bullet point 3: lý do hoặc context
```

**Ví dụ ĐÚNG:**

```
chore: thêm 10 rule files (.agents/rules/) — adapt từ templates cho Pyng

- ai-context: đọc PROJECT_CONTEXT + DEV_ROADMAP trước mỗi task
- architecture: tách biệt handler/service/api layers
- code-style: PEP 8, type hints, Google docstrings
- security: bot auth, RLS, input validation
- naming-conventions: Python + Telegram + Supabase naming
```

**Ví dụ SAI:**

```
chore: thêm 10 rule files
```

→ Thiếu body, không biết thêm gì, tại sao

## Branching

- `main` — production, luôn deployable
- Deploy tự động khi push main (Vercel)

## Pre-commit

- Verify syntax: `python3 -m py_compile <files>`
- Check git status: `git status` trước mỗi task mới
- KHÔNG commit code có errors
