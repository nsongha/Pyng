---
description: Testing guidelines, khi nào đề xuất test, verification trước commit
---

# Testing

## Phân vùng testing

| Workflow           | Kiểm tra gì                                   | Tools                         |
| ------------------ | --------------------------------------------- | ----------------------------- |
| `/task-completion` | Code **chạy được** (syntax, import, deploy)   | `py_compile`, `vercel --prod` |
| `/code-review`     | Code **viết tốt** (security, quality, naming) | Đọc code, so checklist P0-P3  |
| `/qc`              | Code **chạy đúng** (scenarios, edge cases)    | Import test, code trace, curl |

## Khi nào đề xuất test

- Logic phức tạp (≥ 3 branches hoặc ≥ 2 external dependencies) → đề xuất unit test hoặc `/qc --run`
- Utility function có nhiều input variations → gợi ý test cases
- Cross-module changes (handler + service + validator) → `/qc --run`
- CRUD đơn giản, UI thuần, config-only → KHÔNG cần test

> Lưu ý: Chỉ **đề xuất**, không tự viết test trừ khi user yêu cầu.

## Test Cases (khi viết)

- Gợi ý bao gồm: happy path, edge cases, error cases
- Ưu tiên test behavior (output), không test implementation (internal state)
- Tham khảo checklist go-live trong `docs/KNOWN_ISSUES.md` cho regression

## Pre-commit Verification

- Verify build thành công trước khi commit
- Chạy existing test suite nếu project đã có tests
- Không commit code có failing tests
