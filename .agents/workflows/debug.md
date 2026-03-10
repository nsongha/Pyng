---
description: Quy trình debug systematic khi gặp lỗi
---

> Quy trình debug systematic — tích hợp skill `systematic-debugging`.

## 0. Check KNOWN_ISSUES trước

- Đọc `docs/KNOWN_ISSUES.md` — bug có thể đã documented + có workaround sẵn
- Search issues theo keyword lỗi đang gặp

## 1. Thu thập thông tin (`systematic-debugging`)

- Đọc error message **đầy đủ** — không chỉ dòng cuối
- Xác định file + line number gây lỗi
- Kiểm tra git log nếu nghi regression:

```bash
git log --oneline -10
```

## 2. Reproduce

- Chạy lại server/app và trigger lỗi
- Ghi lại exact steps để reproduce
- Xác định: lỗi xảy ra **luôn** hay **intermittent**?

## 3. Isolate

- Thu hẹp phạm vi: module nào gây lỗi?
- Thêm `logging.debug()` tạm tại các điểm nghi ngờ (follow `python-pro`)
- Kiểm tra data flow: input → processing → output
- **Supabase issues:** check RLS policies, connection string (`postgres-best-practices`)
- **Telegram API issues:** check rate limits, webhook status (`telegram-bot-builder`)
- **Async issues:** check deadlocks, missing await (`async-python-patterns`)

## 4. Fix

- Sửa đúng root cause, không patch symptoms
- Chỉ sửa trong phạm vi bug — không refactor kèm
- Follow skill tương ứng với domain bị lỗi

## 5. Verify

- Confirm bug đã fix — chạy lại steps ở bước 2
- Kiểm tra không gây regression ở chỗ khác
- Update `docs/KNOWN_ISSUES.md` nếu phát hiện edge case mới
