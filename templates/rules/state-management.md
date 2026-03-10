---
description: Rules phân chia state giữa Zustand, TanStack Query, React Hook Form
---

# State Management Rules

## Quy tắc phân chia

| Loại state              | Tool                | Ví dụ                              |
| ----------------------- | ------------------- | ---------------------------------- |
| Server state (API data) | **TanStack Query**  | Danh sách bookings, customer info  |
| UI state (global)       | **Zustand**         | Sidebar open, active theme         |
| UI state (local)        | **useState**        | Modal open, dropdown expanded      |
| Form state              | **React Hook Form** | Input values, validation errors    |
| URL state               | **searchParams**    | Page number, search query, filters |

## Rules

1. **Server data KHÔNG ĐƯỢC lưu trong Zustand** — dùng TanStack Query
2. **Local UI state dùng useState** — KHÔNG tạo Zustand store cho state chỉ dùng trong 1 component
3. **URL-persisted state dùng searchParams** — filters, pagination, search
4. **Zustand chỉ cho cross-component UI state** — sidebar, theme, user preferences
5. **KHÔNG derived state trong store** — tính toán trong component hoặc selector

## Cảnh báo

- ⚠️ Nếu thấy `set({ data: apiResponse })` trong Zustand → sai pattern, dùng TanStack Query
- ⚠️ Nếu Zustand store > 10 properties → tách thành nhiều stores
- ⚠️ Nếu subscribe toàn bộ store → dùng selectors
