# Debug Workflow

> Quy trình debug systematic khi gặp lỗi.

## 1. Thu thập thông tin

- Đọc error message đầy đủ
- Xác định file + line number gây lỗi
- Kiểm tra git log xem commit nào gây ra (nếu regression):

```bash
git log --oneline -10
```

## 2. Reproduce

- Chạy lại server/app và trigger lỗi
- Ghi lại exact steps để reproduce

## 3. Isolate

- Thu hẹp phạm vi: module nào gây lỗi?
- Thêm `console.log` tạm tại các điểm nghi ngờ
- Kiểm tra data flow: input → processing → output

## 4. Fix

- Sửa đúng root cause, không patch symptoms
- Chỉ sửa trong phạm vi bug — không refactor kèm

## 5. Verify

- Confirm bug đã fix
- Kiểm tra không gây regression ở chỗ khác
- Chạy test suite (nếu có)
