---
description: Performance optimization guidelines cho Next.js và NestJS
---

# Performance Rules

## Frontend (Next.js)

### Images

- LUÔN dùng `next/image` — tự optimize, lazy load
- Specify `width` và `height` hoặc `fill`
- Dùng `priority` cho above-the-fold images

### Code Splitting

- `next/dynamic` cho heavy components (charts, editors, date pickers)
- Direct imports, KHÔNG barrel files cho components
- Route-based splitting tự động bởi Next.js

### Rendering

- Prefer Server Components (default) cho static/data-fetching
- Client Components chỉ khi cần: event handlers, hooks, browser APIs
- `Suspense` boundaries cho streaming
- `loading.tsx` cho route-level loading states

### Data Fetching

- Parallel fetching với `Promise.all()`
- TanStack Query `staleTime` config hợp lý (30s-5min cho dashboard data)
- Prefetch data on hover cho links

### Memoization

- `useMemo` chỉ cho expensive computations
- `useCallback` chỉ khi truyền callback vào memoized child
- KHÔNG memo mọi thứ — React đã optimize đủ cho hầu hết cases

## Backend (NestJS)

### Database

- Indexes cho columns thường query/filter
- Pagination bắt buộc cho list endpoints
- `select` specific fields, KHÔNG query toàn bộ entity
- N+1: dùng `include` hoặc batch queries

### Caching

- Redis cho session data, rate limiting
- HTTP cache headers cho static resources
- In-memory cache cho config, lookups ít thay đổi

### API Response

- Gzip compression enabled
- Response chỉ chứa fields cần thiết (DTO transform)
- Batch operations cho bulk updates

## Anti-patterns

- ❌ `useEffect` để sync state (dùng derived state)
- ❌ Load toàn bộ data rồi filter client-side
- ❌ Inline styles cho static values (dùng CSS Modules)
- ❌ Unoptimized images (raw URLs không qua next/image)
- ❌ Nested includes > 3 levels trong Prisma
