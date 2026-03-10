---
description: TypeScript best practices, type safety, interface definitions
---

# TypeScript

## Type Safety

- Không dùng `any` — dùng `unknown` nếu cần escape hatch
- Nếu `unknown` chưa đủ → dùng type assertion có kèm runtime check

## Định nghĩa Types

- Luôn define interface/type rõ ràng cho data structures (API response, props, state)
- Prefer `interface` cho object shapes, `type` cho unions/intersections
- Đặt types trong file riêng (`types.ts`) hoặc cùng file nếu chỉ dùng nội bộ

## Type Inference

- Prefer type inference khi TypeScript tự suy luận chính xác
- Dùng explicit annotation khi:
  - Function return type không rõ ràng
  - Complex objects / nested structures
  - Public API / exported functions
