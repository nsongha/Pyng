---
description: Quy tắc đặt tên cho files, components, hooks, CSS, API
---

# Naming Conventions

## Files & Folders

| Loại            | Convention                 | Ví dụ                      |
| --------------- | -------------------------- | -------------------------- |
| React component | PascalCase                 | `BookingCard.tsx`          |
| React page      | kebab-case folder          | `app/bookings/page.tsx`    |
| Hook            | camelCase, prefix `use`    | `useBookings.ts`           |
| Utility         | camelCase                  | `formatDate.ts`            |
| CSS Module      | PascalCase.module.css      | `BookingCard.module.css`   |
| NestJS module   | kebab-case folder          | `modules/bookings/`        |
| NestJS file     | kebab-case                 | `bookings.service.ts`      |
| DTO             | PascalCase, suffix Dto     | `CreateBookingDto`         |
| Test file       | thêm `.spec.ts`/`.test.ts` | `bookings.service.spec.ts` |
| Constants       | UPPER_SNAKE_CASE           | `MAX_BOOKING_DURATION`     |
| Enum values     | UPPER_SNAKE_CASE           | `BookingStatus.CONFIRMED`  |

## React Components

- 1 component = 1 file (trừ sub-components nhỏ dùng nội bộ)
- Component name = file name
- Props interface: `ComponentNameProps`

```typescript
// BookingCard.tsx
interface BookingCardProps {
  booking: Booking;
  onConfirm: (id: string) => void;
}
export function BookingCard({ booking, onConfirm }: BookingCardProps) {}
```

## CSS Classes

- CSS Modules: camelCase trong file CSS → `styles.cardWrapper`
- BEM nếu cần nesting: `card__header`, `card__body`
- KHÔNG viết tắt khó hiểu: ❌ `bkgCrd` → ✅ `bookingCard`

## API Endpoints

- URL: kebab-case, plural nouns → `/api/v1/service-categories`
- Controller method: camelCase verbs → `findAll()`, `createOne()`
- Query params: camelCase → `?branchId=1&sortBy=createdAt`

## Database

- Table names: PascalCase (Prisma convention) → `Booking`, `ServiceCategory`
- Column names: camelCase → `createdAt`, `tenantId`
- Relation fields: camelCase, singular → `customer`, `branch`
