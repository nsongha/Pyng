# Known Issues — [Tên Dự Án]

> Cập nhật lần cuối: YYYY-MM-DD
> Xem lịch sử thay đổi: [CHANGELOG.md](../CHANGELOG.md) | Kế hoạch phát triển: [DEV_ROADMAP.md](DEV_ROADMAP.md)

---

## 🔴 Đang hoạt động (Active)

### [KI-001] [Tiêu đề ngắn gọn]

- **Mức độ**: Critical / Medium / Low
- **Module**: `path/to/module`
- **Mô tả**: [Mô tả chi tiết: điều kiện xảy ra, behavior hiện tại vs expected]
- **Workaround**: [Cách xử lý tạm thời nếu có]
- **Liên quan**: [Phase / Task ID nếu có]

---

### [KI-002] [Tiêu đề]

- **Mức độ**: Medium
- **Module**: `path/to/module`
- **Mô tả**: [Mô tả]
- **Workaround**: [Workaround]

---

## 🟡 Tech Debt

### [TD-001] [Tiêu đề tech debt]

- **Mức độ**: Medium / Low
- **Module**: `path/to/module`
- **Mô tả**: [Mô tả vấn đề tech debt]
- **Kế hoạch fix**: [Phase / milestone dự kiến fix]

---

## ✅ Đã giải quyết gần đây

| ID      | Mô tả                | Giải quyết trong  |
| ------- | -------------------- | ----------------- |
| KI-F001 | [Mô tả issue đã fix] | [Phase / version] |
| KI-F002 | [Mô tả issue đã fix] | [Phase / version] |

---

## 📋 Hướng dẫn báo cáo issue mới

Khi phát hiện bug mới, thêm entry theo format sau vào section **Đang hoạt động**:

```markdown
### [KI-XXX] Tiêu đề ngắn gọn

- **Mức độ**: Critical / Medium / Low
- **Module**: `path/to/module`
- **Mô tả**: Mô tả chi tiết: điều kiện xảy ra, behavior hiện tại vs expected.
- **Workaround**: Cách xử lý tạm thời nếu có.
- **Liên quan**: Phase / Task ID (nếu có)
```

> Xem thêm: [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) — [TASK_BOARD.md](TASK_BOARD.md)
