---
description: Quy trình update documentation trước và sau khi triển khai tính năng
---

# Docs Update Workflow

Mỗi khi triển khai tính năng mới, **BẮT BUỘC** update docs theo 2 bước:

## Bước 1 — Trước khi code (`docs:pre`)

Cập nhật **trước** khi bắt đầu triển khai:

1. `docs/APP_DESCRIPTION.md`:
   - Đánh dấu Phase hiện tại → **🔄 Đang triển khai**
   - Liệt kê các tính năng dự kiến triển khai

2. Commit riêng:

```bash
git add docs/APP_DESCRIPTION.md
git commit -m "docs: plan Phase X — [mô tả ngắn]"
```

## Bước 2 — Sau khi verify (`docs:post`)

Cập nhật **sau** khi verify xong, trước khi commit cuối:

1. `docs/APP_DESCRIPTION.md`:
   - Đánh dấu Phase → **✅ Hoàn thành — vX.Y.Z**
   - Cập nhật chi tiết thực tế (có thể khác plan ban đầu)
   - Thêm Phase tiếp theo nếu có

2. `CHANGELOG.md`:
   - Thêm version mới với danh sách tính năng
   - Di chuyển items từ `[Unreleased]` xuống version

3. `README.md`:
   - Update nếu có tính năng/hướng dẫn mới
   - Update screenshot nếu UI thay đổi đáng kể

4. Commit:

```bash
git add docs/ CHANGELOG.md README.md
git commit -m "docs: complete Phase X — v0.X.0"
```

## Checklist nhanh

```
[ ] docs:pre  — APP_DESCRIPTION: Phase → 🔄
[ ] ...code + verify...
[ ] docs:post — APP_DESCRIPTION: Phase → ✅
[ ] docs:post — CHANGELOG: thêm version
[ ] docs:post — README: update nếu cần
[ ] commit docs riêng
```
