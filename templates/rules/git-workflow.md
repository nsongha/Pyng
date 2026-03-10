---
description: Git commit workflow, conventional commits, documentation updates
---

# Git Workflow

## Sau khi hoàn thành task

- Có thay đổi code → BẮT BUỘC chạy workflow `/task-completion`
- Verify build TRƯỚC khi commit → chạy existing tests nếu có

## Commit Message

- Luôn bằng tiếng Việt
- Theo Conventional Commits:
  - `feat:` tính năng mới
  - `fix:` sửa bug
  - `refactor:` tái cấu trúc không đổi behavior
  - `docs:` cập nhật tài liệu
  - `chore:` công việc hỗ trợ (deps, config...)
- Ví dụ: `feat: thêm bộ lọc theo hạng khách hàng`

## Documentation

- Cập nhật `APP_DESCRIPTION.md` và `CHANGELOG.md` nếu có thay đổi đáng kể
- CHANGELOG entry bằng tiếng Việt, ghi rõ ngày và nội dung thay đổi
