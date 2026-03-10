---
description: Rules cho pnpm monorepo workspace
---

# Monorepo Conventions

## Workspace Structure

- `apps/web` — Next.js frontend (port 3000)
- `apps/api` — NestJS backend (port 3001)
- `packages/shared` — Shared types, constants, utilities

## Import Rules

- ✅ `apps/*` có thể import từ `packages/shared`
- ❌ `apps/web` KHÔNG import từ `apps/api` (chỉ HTTP calls)
- ❌ `packages/shared` KHÔNG import từ `apps/*`
- ❌ KHÔNG cross-import giữa `apps/web` và `apps/api`

## Chung cho packages/shared

- Chỉ chứa: types, interfaces, enums, constants, pure utility functions
- KHÔNG chứa: React components, NestJS decorators, hoặc bất kỳ framework-specific code
- Export qua `index.ts` barrel file (chấp nhận vì shared package nhỏ)

## Scripts Convention

- `pnpm dev` — start tất cả services
- `pnpm build` — build tất cả packages
- `pnpm lint` — lint toàn workspace
- `pnpm dev:web` — chỉ start frontend
- `pnpm dev:api` — chỉ start backend
- `pnpm db:migrate` — Prisma migrate

## Dependencies

- Dependencies dùng chung (TypeScript, ESLint) — root `package.json`
- Dependencies riêng cho app — app-level `package.json`
- KHÔNG duplicate dependencies giữa root và app level

## Khi tạo package mới

1. Tạo folder trong `packages/`
2. Tạo `package.json` với `name: "@spamana/package-name"`
3. Thêm vào `pnpm-workspace.yaml`
4. Verify: `pnpm install`
