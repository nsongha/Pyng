---
name: brainstorming
description: Quy trình brainstorm ý tưởng thành design trước khi code. Dùng khi bắt đầu feature mới, đánh giá approaches, hoặc cần design decisions.
---

# Brainstorming Ideas Into Designs

## Overview

Mọi feature đều cần design — dù "đơn giản". Design có thể ngắn (vài câu), nhưng **PHẢI** trình user approve trước khi code.

**Dùng khi:**

- Bắt đầu feature mới chưa rõ approach
- User hỏi "nên làm thế nào?"
- Có nhiều cách implement, cần chọn
- Phase mới trong DEV_ROADMAP

## Checklist (theo thứ tự)

1. **Explore context** — đọc docs, code hiện tại, recent commits
2. **Hỏi clarifying questions** — 1 câu/lần, multiple choice khi có thể
3. **Đề xuất 2-3 approaches** — kèm tradeoffs và recommendation
4. **Trình design** — từng section, user approve từng phần
5. **Ghi lại quyết định** — vào `docs/DECISIONS.md`
6. **Chuyển sang implementation** — invoke writing-plans skill

## Quy trình chi tiết

### Understanding the idea

- Check project state: files, docs, recent commits
- Đánh giá scope: nếu quá lớn → tách thành sub-projects trước
- Hỏi 1 câu/lần để refine:
  - Purpose: tính năng này giải quyết vấn đề gì?
  - Constraints: giới hạn kỹ thuật? timeline?
  - Success criteria: thế nào là "done"?

### Exploring approaches

- **Luôn đề xuất ≥ 2 approaches** với:
  - Mô tả ngắn
  - Pros/Cons
  - Effort estimate
  - Recommendation + lý do

**Ví dụ:**

```markdown
## Approach A: GPS-only check-in

- ✅ Đơn giản, nhanh implement
- ❌ Không chính xác trong nhà
- Effort: 2 ngày

## Approach B: GPS + WiFi hybrid

- ✅ Chính xác, fallback tốt
- ❌ Phức tạp hơn, cần maintain whitelist
- Effort: 4 ngày

**Recommendation:** Approach B — độ chính xác quan trọng hơn cho check-in.
```

### Presenting the design

- Trình từng section, user approve trước khi tiếp:
  1. Architecture / Component overview
  2. Data flow / Database changes
  3. Bot conversation flow
  4. Error handling
  5. Testing strategy

### Design for Pyng

- **Separation of concerns**: handler → service → database
- **Telegram UX**: inline keyboards, markdown formatting, emoji
- **Serverless-friendly**: stateless, fast cold start
- **Supabase-first**: RLS, REST API, realtime khi cần

## After Design

1. Ghi quyết định vào `docs/DECISIONS.md` (WHY + tradeoff)
2. Invoke `writing-plans` skill để tạo implementation plan
3. Execute plan bằng `/new-feature` hoặc `/parallel-phase`

## Key Principles

- **1 câu hỏi / lần** — không overwhelm user
- **Multiple choice preferred** — dễ answer hơn open-ended
- **YAGNI ruthlessly** — loại bỏ features không cần thiết
- **Explore alternatives** — luôn ≥ 2 approaches trước khi chọn
- **Incremental validation** — trình design, approve, rồi mới code
