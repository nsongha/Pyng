---
description: Performance optimization cho Vercel serverless và Supabase
---

# Performance Rules

## Vercel Serverless

### Cold Start

- Minimize imports — chỉ import cần thiết
- Lazy import cho heavy dependencies
- Keep `requirements.txt` gọn — ít deps = fast cold start
- Function size nhỏ → fast deployment

### Execution Time

- Vercel free tier: 10s timeout → optimize cho < 5s
- Async operations khi có thể
- KHÔNG chạy long-running tasks trong serverless → dùng scheduled jobs

## Supabase / Database

### Queries

- Indexes cho columns thường query/filter (telegram_id, office_id, date)
- Pagination bắt buộc cho list endpoints
- Select specific fields, KHÔNG `SELECT *`
- Dùng RLS policies cho security, không filter trong application code

### Connection

- Dùng REST API (Supabase client) thay vì direct connection khi có thể
- Connection pooling nếu dùng SQLAlchemy

## Telegram Bot

### Response Time

- Reply nhanh (< 3s) → user không thấy lag
- Nếu xử lý lâu → gửi "⏳ Đang xử lý..." trước, rồi edit message
- Batch database operations khi có thể

### Rate Limiting

- Telegram API: 30 msg/s cho group, 1 msg/s cho user
- Queue messages nếu cần gửi nhiều
- Exponential backoff khi bị rate limited

## Anti-patterns

- ❌ Import toàn bộ library khi chỉ cần 1 function
- ❌ Synchronous DB calls trong async handler
- ❌ Fetch tất cả records rồi filter trong Python
- ❌ Không có indexes trên columns thường query
- ❌ Multiple sequential API calls khi có thể parallel
