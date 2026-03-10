---
description: Quy trình phát triển tính năng mới từ analyze đến deploy
---

# New Feature Development

## 1. Phân tích yêu cầu

- Đọc kỹ requirement / user story
- Xác định scope: modules nào bị ảnh hưởng?
- Liệt kê dependencies (database schema thay đổi? service mới?)
- Hỏi lại nếu yêu cầu chưa rõ → KHÔNG tự suy diễn

## 2. Planning

- Lập danh sách files cần tạo/sửa
- Xác định thứ tự: database schema → services → bot handlers → tests
- Tạo implementation plan nếu feature phức tạp

## 3. Database (nếu cần)

// turbo

- Tạo migration mới: `supabase migration new <tên_migration>`
- Viết SQL schema changes
  // turbo
- Push migration: `supabase db push --yes`
- Verify bằng REST API hoặc `supabase db dump`
- Seed data nếu cần cho testing

## 4. Services (nếu cần)

- Tạo/update service trong `services/`
- Implement business logic (tách khỏi handler)
- Dùng Supabase REST API hoặc SQLAlchemy
- Type hints đầy đủ
- Error handling rõ ràng

## 5. Bot Handlers

- Tạo/update handler trong `bot/handlers/`
- Register handler trong `bot/app.py`
- Inline keyboard cho navigation phức tạp
- Error messages thân thiện bằng tiếng Việt
- Parse mode = Markdown cho formatting

## 6. API Endpoints (nếu cần)

- Tạo file trong `api/`
- Vercel auto-detect serverless function
- Auth/validation middleware

## 7. Verification

// turbo

- `python3 -m py_compile <files>` — verify syntax
  // turbo
- `vercel --prod --yes` — deploy thành công
- Test trên Telegram: gửi commands, verify responses
- Check edge cases (empty input, invalid data, unauthorized)

## 8. Commit & Docs

- Chạy workflow `/task-completion`
- Commit message: `feat: <mô tả tiếng Việt>`
