---
description: Tách biệt business logic và handler/UI layer
---

# Architecture Rules

## Separation of Concerns

- **Bot handlers** (`bot/handlers/`): CHỈ parse input, gọi service, format response
- **Services** (`services/`): Business logic, database queries, validation
- **API endpoints** (`api/`): Nhận HTTP request, gọi service, trả response
- **Config** (`config/`): Environment variables, settings
- **Validators** (`validators/`): Input validation rules

## Rules

1. Handler KHÔNG chứa business logic — delegate cho service
2. Service KHÔNG import telegram objects — nhận plain data, trả plain data
3. Database queries CHỈ nằm trong service layer
4. Config được inject qua `config/settings.py`, KHÔNG đọc `os.environ` trực tiếp trong handler

## File Organization

```
bot/
  handlers/     # Telegram command/callback handlers
  keyboards/    # Inline keyboard builders
  app.py        # Application factory
services/       # Business logic
api/            # Vercel serverless functions
config/         # Settings, constants
validators/     # Input validation
db/             # Schema SQL, migrations
```
