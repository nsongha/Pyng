# [Tên Dự Án] — Project Context

> Đọc file này trước khi làm bất cứ việc gì. Cập nhật lần cuối: YYYY-MM-DD

## Project Overview

- **Mô tả**: [Mô tả ngắn 1-2 câu về dự án]
- **Mô hình**: [Internal tool / SaaS / Consumer app]
- **Đối tượng**: [Target users]
- **Deployment**: [Local / Cloud / Hybrid]

## Tech Stack

| Layer       | Technology         | Version / Notes |
| ----------- | ------------------ | --------------- |
| Backend     | [framework]        | [version]       |
| Frontend    | [framework]        | [version]       |
| Database    | [DB]               | [version]       |
| Testing     | [test framework]   | [version]       |
| Linting     | [linter]           | [version]       |
| Data Source | [sources]          | [notes]         |
| Caching     | [cache strategy]   | [TTL, notes]    |
| Config      | [config mechanism] | [notes]         |

## Architecture

- **Cấu trúc repo**: [Monorepo / Multi-repo, thư mục chính]
- **API format**: [REST / GraphQL] — base URL `http://localhost:<port>/api`
- **Data flow**: `[Client] ←→ [Server] ←→ [Data Sources]`
- **Dev mode**: [Dev mode behaviors]

## Modules hiện có

### Backend (`src/`)

<!-- Liệt kê các modules chính với mô tả ngắn -->

- `src/server.mjs` — [mô tả]
- `src/utils/...` — [mô tả]
- `src/collectors/...` — [mô tả]

### Frontend (`public/` hoặc `client/`)

- `public/index.html` — [mô tả]
- `public/js/app.mjs` — [mô tả]

### Scripts & Config

- `scripts/...` — [mô tả]
- `config.json` — [mô tả]

### Tests (`tests/`)

- `tests/...` — [mô tả coverage]

### Documentation (`docs/`)

- `docs/PROJECT_CONTEXT.md` — File này
- `docs/APP_DESCRIPTION.md` — Features & roadmap
- `docs/DECISIONS.md` — Architecture decisions
- `docs/KNOWN_ISSUES.md` — Bugs đã biết

## API Endpoints

| Method | Path       | Mô tả   |
| ------ | ---------- | ------- |
| GET    | `/api/...` | [mô tả] |
| POST   | `/api/...` | [mô tả] |

## Data Sources

| Source     | Data            |
| ---------- | --------------- |
| [source 1] | [data provided] |
| [source 2] | [data provided] |

## Current Status

- **Version**: [X.Y.Z]
- **Phase**: [Phase hiện tại]
- **Unreleased changes**: [Liệt kê changes chưa release]
- **Next milestone**: [Mục tiêu tiếp theo]

## Key Conventions

- **Commit format**: Conventional Commits
- **Naming**: camelCase cho variables, kebab-case cho files
- **Modules**: ES Modules (`import/export`)
- **Config**: [Mô tả cách quản lý config]

## Docs Reference

| Cần thông tin về        | Đọc file                                 |
| ----------------------- | ---------------------------------------- |
| Full features & roadmap | [APP_DESCRIPTION.md](APP_DESCRIPTION.md) |
| Kế hoạch phát triển     | [DEV_ROADMAP.md](DEV_ROADMAP.md)         |
| Tiến độ phase           | [TASK_BOARD.md](TASK_BOARD.md)           |
| Lịch sử thay đổi        | [CHANGELOG.md](../CHANGELOG.md)          |
| Bugs đã biết            | [KNOWN_ISSUES.md](KNOWN_ISSUES.md)       |
| Quyết định kiến trúc    | [DECISIONS.md](DECISIONS.md)             |

## Context Size Guide

- Chỉ đọc file này: ~X lines
- - APP_DESCRIPTION.md: ~+Y lines
- Ngưỡng cảnh báo: > 300 lines tổng → cân nhắc trim context
