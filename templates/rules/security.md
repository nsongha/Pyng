---
description: Bảo mật cơ bản, secrets management, input validation
---

# Security

## Secrets & Credentials

- Không hardcode secrets, API keys, credentials vào source code
- Sử dụng environment variables (`.env`, `.env.local`)
- File `.env` phải nằm trong `.gitignore`

## Input Validation

- Validate và sanitize mọi input từ user hoặc external source
- Không trust client-side validation — luôn validate phía server

## Proactive Alerts

- Nhắc nhở khi phát hiện potential security issue — dù không được hỏi
- Ví dụ: SQL injection risk, XSS vulnerability, exposed sensitive data
