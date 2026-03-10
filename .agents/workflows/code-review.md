---
description: Quy trình code review tự động dựa trên code-review-checklist skill
---

# /code-review — Automated Code Review

> Dùng khi: hoàn thành 1 phase, trước khi release, hoặc khi muốn kiểm tra chất lượng code.

## 1. Xác định scope review

// turbo

```bash
git diff --name-only HEAD~1
```

- Liệt kê files đã thay đổi
- Xác định modules bị ảnh hưởng
- Nếu > 20 files → chia theo module, review từng nhóm

## 2. Đọc context

- Đọc `docs/PROJECT_CONTEXT.md` → hiểu project conventions
- Đọc `docs/KNOWN_ISSUES.md` → tránh report lại issue đã biết
- Đọc `docs/DECISIONS.md` → hiểu tại sao code viết theo cách hiện tại

## 3. Review theo checklist

Duyệt theo thứ tự ưu tiên (dừng ngay nếu có P0):

### P0 — Security (block release)

- [ ] Input validation trên MỌI user input (Telegram messages, callback data)
- [ ] Không hardcode secrets/credentials (bot token, db password)
- [ ] SQL injection prevention (parameterized queries / ORM)
- [ ] Telegram user ID validation trên mọi handler
- [ ] Không expose sensitive data trong bot responses
- [ ] Webhook endpoint chỉ accept Telegram requests

### P1 — Functionality & Correctness

- [ ] Code giải quyết đúng vấn đề đặt ra
- [ ] Edge cases: null, empty, boundary values
- [ ] Error states có response/UI phù hợp
- [ ] Không break backward compatibility
- [ ] Type hints đầy đủ (Python typing)
- [ ] Async/await dùng đúng (không block event loop)

### P2 — Code Quality & Performance

- [ ] Single Responsibility — mỗi function/file 1 việc
- [ ] Naming rõ ràng, self-documenting
- [ ] Không N+1 queries
- [ ] File size hợp lý (< 300 dòng)
- [ ] Business logic tách khỏi handler/controller

### P3 — Documentation & Tests

- [ ] Commit message theo Conventional Commits
- [ ] Docstrings cho functions phức tạp
- [ ] docs/ updated (nếu command mới)

## 4. Output Report

Tạo report theo format:

```markdown
## Code Review Report — [Phase/Feature]

**Scope**: N files, M modules
**Date**: YYYY-MM-DD

### 🔴 P0 — Critical (block release)

- [file:line] Mô tả issue + đề xuất fix

### 🟠 P1 — Important

- [file:line] Mô tả issue + đề xuất fix

### 🟡 P2 — Improvement

- [file:line] Mô tả issue

### 🟢 P3 — Nitpick

- [file:line] Mô tả

### Summary

- P0: X issues (PHẢI fix trước release)
- P1: X issues (nên fix)
- P2: X issues (fix khi rảnh)
- P3: X issues (optional)
```

## 5. Action

- **Có P0** → DỪNG, fix NGAY, chạy `/task-completion`
- **Chỉ P1** → Tạo task fix, có thể release nếu urgent
- **Chỉ P2/P3** → Ghi vào `docs/KNOWN_ISSUES.md` mục Tech Debt, release bình thường

## LƯU Ý

- KHÔNG review style/formatting — đó là việc của linter
- KHÔNG review code ngoài scope (chỉ xem diff)
- Focus vào **behavior correctness** và **security**, không phải personal preference
- Nếu phát hiện pattern lặp lại → đề xuất thêm vào skill hoặc lint rule
