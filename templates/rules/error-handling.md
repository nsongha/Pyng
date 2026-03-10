---
description: Xử lý lỗi, guard clauses, error/loading states
---

# Error Handling

## Guard Clauses & Early Return

- Dùng guard clauses + early return — tránh nested if sâu
- Handle edge cases ngay đầu function
- Ưu tiên "fail fast" — điều kiện không hợp lệ → return/throw ngay

```typescript
// ✅ Tốt: guard clause
function processOrder(order: Order) {
  if (!order) return null;
  if (!order.items.length) return { error: 'Empty order' };

  // Happy path logic here...
}

// ❌ Tránh: nested if
function processOrder(order: Order) {
  if (order) {
    if (order.items.length) {
      // Logic bị đẩy sâu vào...
    }
  }
}
```

## UI Error States

- Không để lộ error message kỹ thuật ra UI (stack trace, SQL error, etc.)
- Hiển thị thông báo thân thiện cho user, log chi tiết ở server/console

## API Calls

- Luôn có error state VÀ loading state cho mọi API call
- Xử lý cả network error lẫn business error
