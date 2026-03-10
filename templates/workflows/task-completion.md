---
description: Quy trình bắt buộc sau khi hoàn thành mỗi task (code, verify, commit, docs)
---

# Task Completion Workflow

## BẮT BUỘC thực hiện sau khi hoàn thành MỌI task có thay đổi code:

### 1. Test (nếu có thay đổi API code)

> **Skip nếu** task CHỈ thay đổi: `docs/`, `apps/web/`, `apps/admin/`, `.agent/`, `infra/`, CSS, config
> **Chạy nếu** có thay đổi trong `apps/api/src/` hoặc `packages/shared/`

// turbo

```bash
pnpm --filter @spamana/api test
```

- Đảm bảo tất cả unit tests pass

### 2. Verify

// turbo

```bash
pnpm --filter @spamana/web build
```

- Đảm bảo build pass, không có TypeScript errors

### 3. Git Commit (code)

- Stage tất cả changes: `git add -A`
- Commit theo Conventional Commits format:
  - `feat:` cho tính năng mới
  - `fix:` cho bug fix
  - `refactor:` cho refactoring
  - `docs:` cho documentation only
  - `chore:` cho tooling, config
- Commit message bằng **tiếng Việt**, mô tả ngắn gọn
- Ví dụ: `feat: thêm badge hạng khách hàng + bộ lọc tier`
- Body (optional): liệt kê các thay đổi chính, cũng bằng tiếng Việt

### 4. Documentation Update — Checklist từng file

> ⚠️ **Kiểm tra TỪNG file** trong danh sách dưới đây. KHÔNG dựa vào cảm giác "đã xong".

**Duyệt qua checklist sau và update NẾU có thay đổi liên quan:**

- [ ] `CHANGELOG.md` — luôn update khi có tính năng mới hoặc fix đáng kể
- [ ] `docs/APP_DESCRIPTION.md` — update khi:
  - Phase status thay đổi (planned → hoàn thành)
  - Có module/tính năng mới
  - Roadmap thay đổi
- [ ] `docs/AI_CONTEXT.md` — update khi:
  - Phase status / version thay đổi
  - Module mới hoặc thay đổi lớn
  - Stack / architecture / convention thay đổi
- [ ] `docs/API_SPEC.md` — update khi có endpoint mới hoặc thay đổi API contract
- [ ] `docs/DATABASE_SCHEMA.md` — update khi có thay đổi Prisma schema
- [ ] `docs/DECISIONS_LOG.md` — update khi có quyết định kiến trúc quan trọng (chọn library, pattern, strategy)
- [ ] `docs/KNOWN_ISSUES.md` — update khi phát hiện bug/tech debt mới, hoặc fix issue đã biết

**Nếu task chỉ là bug fix nhỏ / UI tweak → chỉ cần `CHANGELOG.md`, bỏ qua các file còn lại.**

Commit docs riêng: `git commit -m "docs: ..."`

### 4.5. Verify Docs — BẮT BUỘC sau khi commit docs

> ⛔ KHÔNG được skip bước này. Đây là gate check cuối cùng trước khi báo cáo user.

// turbo

```bash
git diff HEAD~1 --name-only
```

**So sánh output với checklist bước 4:**

1. Nếu task có **tính năng mới / phase mới** → `CHANGELOG.md` + `APP_DESCRIPTION.md` + `AI_CONTEXT.md` **BẮT BUỘC** phải xuất hiện trong diff
2. Nếu task có **endpoint mới** → `API_SPEC.md` phải xuất hiện
3. Nếu task có **schema change** → `DATABASE_SCHEMA.md` phải xuất hiện

**Nếu thiếu file nào:**

- DỪNG LẠI, update file bị thiếu
- `git add` + `git commit --amend --no-edit` để gộp vào commit docs
- Chạy lại bước 4.5 để verify

### 5. Summary

- Báo cáo cho user:
  - Những gì đã làm
  - Build status
  - Files changed
  - Commit hash

## LƯU Ý QUAN TRỌNG

- KHÔNG chờ user yêu cầu mới commit — commit NGAY sau khi verify pass
- KHÔNG để changes uncommitted qua nhiều tasks
- Mỗi task = 1 commit (hoặc tối đa 2: code + docs)
- Luôn kiểm tra `git status` trước khi bắt đầu task mới
