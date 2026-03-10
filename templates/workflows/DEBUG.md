---
description: Quy trình debug có hệ thống dựa trên systematic-debugging skill
---

# Debug Workflow

> Tham khảo chi tiết skill `@systematic-debugging` trước khi bắt đầu.

## 1. Reproduce

- Xác nhận bug: reproduce được bằng steps cụ thể
- Ghi lại: URL, input, expected vs actual behavior
- Screenshot / error log nếu có

## 2. Root Cause Investigation

// turbo

- Đọc error logs, stack traces
- Kiểm tra recent changes: `git log -5 --oneline`
- Trace execution path từ input → output
- Xác định scope: frontend? backend? database? infra?

### Frontend debug

// turbo

- Browser DevTools → Console errors
- Network tab → API responses
- React DevTools → component tree, state
- Zustand DevTools → store state changes

### Backend debug

// turbo

- NestJS logs → controller/service errors
- Prisma query logs → database issues
- Check Guards/Interceptors pipeline
- Verify JWT payload và tenantId

## 3. Hypothesis

- Đặt giả thuyết: "Lỗi vì [X] xảy ra khi [Y]"
- Viết test reproduce lỗi (nếu áp dụng TDD)
- Verify giả thuyết bằng evidence

## 4. Fix

- Fix ĐÚNG root cause, KHÔNG fix symptom
- Phạm vi fix tối thiểu — KHÔNG refactor thêm
- Thêm test case cover trường hợp gây lỗi

## 5. Verify

// turbo

- Bug không còn reproduce
  // turbo
- `pnpm build` pass
- Existing tests pass
- Kiểm tra side effects trên modules liên quan

## 6. Commit

- Chạy workflow `/task-completion`
- Commit message: `fix: <mô tả lỗi đã sửa tiếng Việt>`
