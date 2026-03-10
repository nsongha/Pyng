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

## Branching

- `main` — production, luôn deployable
- Deploy tự động khi push main (Vercel)

## Pre-commit

- Verify syntax: `python3 -m py_compile <files>`
- Check git status: `git status` trước mỗi task mới
- KHÔNG commit code có errors
