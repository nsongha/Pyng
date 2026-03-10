---
description: Quy tắc đặt tên cho files, functions, variables, database
---

# Naming Conventions

## Files & Folders

| Loại          | Convention       | Ví dụ                    |
| ------------- | ---------------- | ------------------------ |
| Python module | snake_case       | `checkin_service.py`     |
| Bot handler   | snake_case       | `bot/handlers/start.py`  |
| Service       | snake_case       | `services/checkin.py`    |
| API endpoint  | snake_case       | `api/webhook.py`         |
| Config        | snake_case       | `config/settings.py`     |
| SQL migration | date_prefix      | `20260311_seed_data.sql` |
| Constants     | UPPER_SNAKE_CASE | `MAX_GEOFENCE_RADIUS`    |
| Test file     | prefix `test_`   | `test_checkin.py`        |

## Python

- Functions/methods: `snake_case` → `validate_location()`
- Classes: `PascalCase` → `CheckinService`
- Constants: `UPPER_SNAKE_CASE` → `DEFAULT_RADIUS_METERS`
- Private: prefix `_` → `_calculate_distance()`
- Async functions: prefix `async` tự nhiên → `async def process_checkin()`

## Telegram Bot

- Command handlers: `<command>_command` → `start_command`, `checkin_command`
- Callback handlers: `<action>_callback` → `approve_callback`
- Keyboard builders: `build_<name>_keyboard` → `build_main_keyboard`

## Database (Supabase)

- Table names: snake_case, plural → `employees`, `checkin_records`
- Column names: snake_case → `created_at`, `telegram_id`
- Foreign keys: `<table_singular>_id` → `employee_id`, `office_id`
- Indexes: `idx_<table>_<column>` → `idx_employees_telegram_id`

## Environment Variables

- UPPER_SNAKE_CASE → `TELEGRAM_BOT_TOKEN`, `SUPABASE_URL`
- Prefix theo service: `SUPABASE_`, `TELEGRAM_`
