# Parallel Phase Execution

> Chia phase lớn thành streams song song — dùng khi phase có > 8 tasks.
> Nếu phase nhỏ (≤ 5 tasks, 1 domain) → dùng DEV workflow thay thế.

## 1. Analyze Phase Scope

- Đọc `docs/PROJECT_CONTEXT.md` → hiểu current status
- Đọc `docs/APP_DESCRIPTION.md` → xem scope phase cần triển khai
- Liệt kê TẤT CẢ features/tasks cần làm
- Ước lượng tổng tasks → nếu > 8 → tiếp tục workflow này

## 2. Chia Streams

Nhóm tasks theo **domain/concern**, KHÔNG theo thứ tự thời gian:

| Stream type      | Ví dụ                                      | Khi nào dùng            |
| ---------------- | ------------------------------------------ | ----------------------- |
| **Server**       | API routes, data collectors, parsers       | Có thay đổi backend     |
| **Frontend**     | Charts, tabs, UI sections                  | Có thay đổi frontend    |
| **CLI**          | Standalone collector                       | Có thay đổi CLI         |
| **Infra/Config** | package.json, config, build                | Có thay đổi config/deps |
| **Performance**  | Caching, optimization                      | Có yêu cầu performance  |
| **UX Polish**    | Error handling, loading states, animations | Có yêu cầu UX           |

**Nguyên tắc chia:**

- Mỗi stream 3-8 tasks (không quá ít, không quá nhiều)
- Tối thiểu file overlap giữa streams
- Xác định shared files → ghi rõ ai sửa trước
- Nếu 1 stream quá lớn → tách thành 2

## 3. Tạo TASK_BOARD.md

Tạo file `TASK_BOARD.md` theo template TASK_BOARD với cấu trúc streams, dependencies, conflict rules.

**Status icons:** 📋 TODO → 🔄 IN PROGRESS → ✅ DONE → ⏸️ BLOCKED

**Priority:** P0 (must have) → P1 (should have) → P2 (nice to have)

## 4. Review & Approve Task Board

- Trình task board cho team/reviewer
- Điều chỉnh streams/tasks nếu cần
- Xác nhận execution order

## 5. Execute

### Prompt template cho mỗi stream:

```
Triển khai Stream [X] ([tên]) trong @TASK_BOARD.md
Làm từ task có priority P0 trước, skip task nào bị BLOCKED.
```

### Rules cho mỗi stream:

1. Đọc PROJECT_CONTEXT trước
2. Đọc TASK_BOARD → hiểu scope + dependencies + context
3. Check Cross-Stream Dependencies trước khi bắt đầu task
4. Update status trên TASK_BOARD khi hoàn thành task (📋 → ✅)
5. Chỉ sửa files trong scope của stream mình
6. Test + verify sau mỗi nhóm tasks
7. KHÔNG tự commit — commit sẽ được gộp ở bước merge

## 6. Verify & Review

Sau khi tất cả streams hoàn thành:

- Verify syntax/build check
- Confirm TASK_BOARD 100%
- Chạy code review trên toàn bộ thay đổi
- Resolve conflicts nếu có

## 7. Finalize

1. Gộp changelog — nhiều stream entries → 1 version entry
2. Update docs — PROJECT_CONTEXT, APP_DESCRIPTION
3. Commit gọn
4. Run task completion workflow

## LƯU Ý

- Phase **≤ 5 tasks** → KHÔNG dùng workflow này
- Phase **6-10 tasks** → optional, có thể chia 2-3 phần đơn giản
- Phase **> 10 tasks** → BẮT BUỘC dùng workflow này
- Ưu tiên **ít file overlap** hơn là cân bằng số tasks
