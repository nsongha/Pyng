---
description: Kiến trúc phần mềm, separation of concerns, quy trình trước khi code
---

# Architecture

## Separation of Concerns

- Tách biệt Logic và UI: Business Logic không được nằm trong Component hiển thị
- Single Responsibility: mỗi file/function chỉ làm 1 việc
- Layer rõ ràng: UI → Hooks/Services → Data Access

## Trước khi code tính năng mới

1. Phân tích kiến trúc, liệt kê file cần tạo/sửa
2. Xác nhận với user trước
3. Sau khi được approve mới viết code

## An toàn khi chỉnh sửa

- KHÔNG xóa hoặc refactor code hiện tại trừ khi được yêu cầu rõ ràng
- Chỉ thay đổi đúng phạm vi được yêu cầu — không "bonus fix" tự ý
- Khi sửa bug: chỉ fix bug đó, không refactor xung quanh
