---
description: Project structure cho Pyng (non-monorepo Python project)
---

# Project Structure

## Folder Layout

```
Pyng/
├── api/              # Vercel serverless functions
│   └── webhook.py    # Telegram webhook endpoint
├── bot/              # Telegram bot code
│   ├── app.py        # Application factory
│   ├── handlers/     # Command & callback handlers
│   └── keyboards/    # Inline keyboard builders
├── services/         # Business logic (tách khỏi handlers)
├── validators/       # Input validation
├── config/           # Settings, constants
│   └── settings.py   # Environment variables reader
├── db/               # Database schema
│   └── schema.sql    # Table definitions
├── supabase/         # Supabase CLI migrations
├── miniapp/          # React Mini App (future)
├── qr/               # QR display page
├── docs/             # Project documentation
├── templates/        # Template rules/workflows (reference)
└── .agents/          # AI agent configuration
    ├── rules/        # Code rules & conventions
    ├── workflows/    # Development workflows
    └── skills/       # AI skills & knowledge
```

## Rules

- KHÔNG tạo files ngoài cấu trúc trên trừ khi có lý do rõ ràng
- Mỗi folder phải có `__init__.py` nếu là Python package
- API endpoints = files trong `api/` (Vercel auto-detect)
- Static files (QR page, assets) → thư mục riêng ở root
