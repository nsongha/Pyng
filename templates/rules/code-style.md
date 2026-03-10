---
description: Quy tắc styling, kích thước file và tái sử dụng code
---

# Code Style

## Styling

- Không dùng TailwindCSS → CSS Modules hoặc Vanilla CSS
- Không inline styles trừ khi dynamic value bắt buộc
  - ✅ OK: `style={{ width: calculatedWidth }}` — giá trị tính toán runtime
  - ❌ Không: `style={{ color: 'red' }}` — dùng CSS class thay thế

## Kích thước file

- File > 200 dòng → đề xuất tách nhỏ
- File > 300 dòng → **bắt buộc** tách

## Tái sử dụng

- UI hoặc Logic dùng lại ≥ 2 lần → tách thành Component hoặc Utility function riêng
- Không duplicate code — trích xuất thành shared module
