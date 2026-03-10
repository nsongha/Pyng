---
description: Khởi động dev server và test bot locally
---

# /dev — Dev Server Workflow

## Vấn đề cần tránh

Vercel functions chạy serverless — mỗi request = 1 invocation riêng.
Khi dev locally, cần dùng polling mode thay vì webhook.

## Quy trình chuẩn

### 1. Setup local venv (lần đầu)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Test bot locally (polling mode)

// turbo

```bash
source .venv/bin/activate
python3 -c "
from bot.app import create_bot
app = create_bot()
print('🤖 Bot running in polling mode...')
app.run_polling()
"
```

> **Lưu ý**: Khi chạy polling, phải TẮT webhook trước:
> `curl https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/deleteWebhook`
> Sau khi test xong, SET LẠI webhook:
> `curl https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook?url=https://pyng.vercel.app/api/webhook`

### 3. Test Vercel functions locally

// turbo

```bash
vercel dev
```

> Truy cập `http://localhost:3000/api/webhook` để test

### 4. Deploy production

// turbo

```bash
vercel --prod --yes
```

## Nguyên tắc

- **Local dev** → polling mode (không cần webhook URL)
- **Production** → webhook mode (Vercel serverless)
- **LUÔN** set lại webhook sau khi test local xong
- Test trên Telegram mobile (iOS/Android) trước khi claim done
