---
description: Testing guidelines, khi nào đề xuất test, verification trước commit
---

# Testing

## Khi nào đề xuất test

- Logic phức tạp (nhiều branch, edge cases) → đề xuất unit test
- Utility function có nhiều input variations → gợi ý test cases
- CRUD đơn giản, UI thuần → KHÔNG cần nhắc test

> Lưu ý: Chỉ **đề xuất**, không tự viết test trừ khi user yêu cầu.

## Test Cases

- Gợi ý bao gồm: happy path, edge cases, error cases
- Ưu tiên test behavior (output), không test implementation (internal state)

## Pre-commit Verification

- Verify build thành công trước khi commit
- Chạy existing test suite nếu project đã có tests
- Không commit code có failing tests
