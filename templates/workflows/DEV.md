---
description: Khởi động và quản lý dev server an toàn, tránh zombie processes
---

# /dev — Dev Server Workflow

## Vấn đề cần tránh

Mỗi lần gõ `pnpm dev` mà KHÔNG tắt session cũ sẽ tạo thêm Node processes chạy ngầm
(zombie processes), gây ra lỗi `EADDRINUSE`, API trả về data cũ, CPU/RAM bị ngốn.

## Quy trình chuẩn

### 1. Trước khi bắt đầu làm việc buổi sáng (hoặc sau khi restart máy)

Kiểm tra xem dev server có đang chạy chưa:

```bash
pnpm lsof -ti:3001
```

Nếu không có output → chưa có server nào, chạy bình thường:

// turbo

```bash
pnpm dev
```

### 2. Khi cần restart (sau khi thay đổi code quan trọng, xử lý lỗi)

Dùng lệnh này thay vì tắt terminal và mở lại:

// turbo

```bash
pnpm restart
```

> **Giải thích**: `pnpm restart` = `pnpm kill` (dọn sạch) + 1 giây chờ + `pnpm dev` (khởi động lại)

### 3. Chỉ dọn sạch (không restart)

// turbo

```bash
pnpm kill
```

## Nguyên tắc sử dụng terminal trong IDE

- **KHÔNG** mở nhiều terminal rồi gõ `pnpm dev` ở mỗi cái — Turborepo tự chạy tất cả apps.
- **CHỈ cần 1 terminal** chạy `pnpm dev` ở thư mục root.
- Khi đóng cửa sổ IDE → terminal tự tắt → Node processes cũng tự chết (bình thường).
- Nếu IDE crash → chạy `pnpm kill` trước khi `pnpm dev`.

## Dấu hiệu nhận biết có zombie process

- `pnpm dev` báo lỗi `EADDRINUSE: address already in use :::3001`
- API/Frontend trả về kết quả không đúng dù đã sửa code
- Máy chạy nóng/chậm bất thường

→ Chạy `pnpm restart` để xử lý.
