---
description: Quy trình debug có hệ thống dựa trên systematic-debugging skill
---

# Debug Workflow

> Tham khảo chi tiết skill `@systematic-debugging` trước khi bắt đầu.

## 1. Reproduce

- Xác nhận bug: reproduce được bằng steps cụ thể
- Ghi lại: Telegram message, input, expected vs actual behavior
- Screenshot / error log nếu có

## 2. Root Cause Investigation

// turbo

- Đọc error logs, stack traces
- Kiểm tra recent changes: `git log -5 --oneline`
- Trace execution path từ input → output
- Xác định scope: bot handler? service? database? Vercel?

### Bot/API debug

// turbo

- Vercel function logs → `vercel logs pyng.vercel.app`
- Telegram webhook info → `curl https://api.telegram.org/bot$TOKEN/getWebhookInfo`
- Test webhook endpoint → `curl -X POST https://pyng.vercel.app/api/webhook -d '...'`
- Check pending updates → `pending_update_count` trong webhook info

### Database debug

// turbo

- Supabase REST API → test query trực tiếp
- Check data integrity → `supabase db dump --data-only`
- Migration status → `supabase migration list`
- RLS policies → verify service_role vs anon key access

## 3. Hypothesis

- Đặt giả thuyết: "Lỗi vì [X] xảy ra khi [Y]"
- Verify giả thuyết bằng evidence (logs, API responses)
- Nếu cần → thêm print/logging tạm để trace

## 4. Fix

- Fix ĐÚNG root cause, KHÔNG fix symptom
- Phạm vi fix tối thiểu — KHÔNG refactor thêm
- Thêm error handling nếu case chưa được xử lý

## 5. Verify

// turbo

- Bug không còn reproduce
  // turbo
- `python3 -m py_compile <fixed_file>` — syntax OK
- Deploy thành công: `vercel --prod --yes`
- Test trên Telegram: gửi command và verify reply
- Kiểm tra side effects trên modules liên quan

## 6. Commit

- Chạy workflow `/task-completion`
- Commit message: `fix: <mô tả lỗi đã sửa tiếng Việt>`
