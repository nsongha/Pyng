---
description: Quy trình update documentation trước và sau khi triển khai tính năng
---

# Docs Update Workflow

Mỗi khi triển khai tính năng mới, **BẮT BUỘC** update docs theo 2 bước:

## Bước 1 — Trước khi code (`docs:pre`)

Cập nhật **trước** khi bắt đầu triển khai:

1. `docs/DEV_ROADMAP.md`:
   - Đánh dấu Phase hiện tại → tasks đang làm `[/]`

2. Commit riêng:

```bash
git add docs/DEV_ROADMAP.md
git commit -m "docs: plan Phase X — [mô tả ngắn]"
```

## Bước 2 — Sau khi verify (`docs:post`)

Cập nhật **sau** khi verify xong, trước khi commit cuối:

1. `docs/DEV_ROADMAP.md`:
   - Đánh dấu Phase → tasks hoàn thành `[x]`, thêm ✅ nếu xong phase

2. `docs/CHANGELOG.md`:
   - Thêm entries vào `[Unreleased]` với danh sách tính năng
   - Di chuyển items sang version khi release

3. `docs/PROJECT_CONTEXT.md`:
   - Update nếu có thay đổi kiến trúc/scope/deploy URL

4. `docs/README.md`:
   - Update nếu có tính năng/hướng dẫn mới
   - Update folder structure nếu thay đổi

5. Commit:

```bash
git add docs/ CHANGELOG.md
git commit -m "docs: complete Phase X — v0.X.0"
```

## Checklist nhanh

```
[ ] docs:pre  — DEV_ROADMAP: tasks → [/]
[ ] ...code + verify...
[ ] docs:post — DEV_ROADMAP: tasks → [x]
[ ] docs:post — CHANGELOG: thêm entries
[ ] docs:post — PROJECT_CONTEXT: update nếu cần
[ ] docs:post — README: update nếu cần
[ ] commit docs riêng
```
