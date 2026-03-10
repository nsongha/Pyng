# Feature Development Workflow

> Workflow phát triển feature mới.

## 1. Đọc context

- Đọc `docs/PROJECT_CONTEXT.md` trước tiên
- Đọc thêm `docs/APP_DESCRIPTION.md` nếu cần hiểu roadmap

## 2. Phân tích yêu cầu

- Feature này thay đổi backend (API), frontend (UI), hay cả hai?
- Có ảnh hưởng tới data format không? (breaking change)
- Cần thêm dependency mới không?

## 3. Plan

- Xác định files cần sửa
- Nếu phức tạp (> 3 files): viết implementation plan trước
- Nếu đơn giản: implement trực tiếp

## 4. Implement

- **Backend changes**: sửa server, thêm route/parser mới
- **Frontend changes**: sửa UI, thêm section/component mới
- **CLI changes**: sync logic vào CLI nếu cần
- Giữ consistent với code style hiện tại

## 5. Test

- Chạy server/app
- Verify trên browser/client
- Test các edge cases

## 6. Hoàn tất

- Chạy code review checklist
- Update CHANGELOG, docs nếu cần
- Commit theo Conventional Commits
