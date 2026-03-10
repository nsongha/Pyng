---
description: Quy trình phát triển tính năng mới từ analyze đến deploy
---

# New Feature Development

## 1. Phân tích yêu cầu

- Đọc kỹ requirement / user story
- Xác định scope: modules nào bị ảnh hưởng?
- Liệt kê dependencies (backend API cần tạo? database schema thay đổi?)
- Hỏi lại nếu yêu cầu chưa rõ → KHÔNG tự suy diễn

## 2. Planning

- Tạo branch: `feat/<tên-tính-năng>` (ví dụ: `feat/booking-calendar`)
- Lập danh sách files cần tạo/sửa
- Xác định thứ tự: shared types → database → backend API → frontend

## 3. Database (nếu cần)

// turbo

- Update Prisma schema
  // turbo
- Tạo migration: `pnpm db:migrate`
- Verify migration apply thành công
- Seed data nếu cần cho testing

## 4. Backend (nếu cần)

- Tạo/update DTOs trong module
- Implement service logic
- Tạo controller endpoints
- Thêm Guards/Pipes nếu cần
  // turbo
- Test API bằng curl hoặc Postman

## 5. Frontend

- Tạo/update types trong `packages/shared` (nếu shared)
- Implement API client function
- Tạo components (UI layer)
- Connect với TanStack Query hooks
- Thêm loading, error, empty states
- CSS Modules cho styling

## 6. Verification

// turbo

- `pnpm build` — verify build thành công
  // turbo
- `pnpm lint` — no lint errors
- Test thủ công các flows chính
- Check responsive (nếu UI changes)

## 7. Commit & Docs

- Chạy workflow `/task-completion`
- Commit message: `feat: <mô tả tiếng Việt>`
- Update `APP_DESCRIPTION.md` nếu feature đáng kể
- Update `CHANGELOG.md`
