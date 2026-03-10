---
description: Rule đọc AI Context trước khi bắt đầu task
globs: ['**/*']
alwaysApply: true
---

# AI Context First

- Khi bắt đầu task mới (implement feature, fix bug, refactor), LUÔN đọc `docs/AI_CONTEXT.md` trước
- File này chứa tóm tắt project: stack, architecture, current phase, conventions
- Chỉ đọc thêm docs chi tiết (APP_DESCRIPTION, DATABASE_SCHEMA, PRD...) khi cần deep-dive
- File AI_CONTEXT.md được auto-maintained bởi `/task-completion` workflow
