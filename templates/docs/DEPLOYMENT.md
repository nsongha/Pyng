# [Tên Dự Án] — Deployment Guide

## Overview

[Tên app] là một ứng dụng [Node.js/Python/...]. Có thể deploy bằng:

- **PM2** (recommended cho production trên VPS/server)
- **Docker** (containerized deployment)
- **Nginx** reverse proxy (cho HTTPS + domain name)

Default port: **[PORT]**

---

## Option 1: PM2 (Recommended)

### Install PM2

```bash
npm install -g pm2
```

### Start

```bash
cd /path/to/project
npm install
pm2 start <entry-file> --name "<app-name>" --interpreter node
pm2 save
pm2 startup
```

### Useful Commands

```bash
pm2 status
pm2 logs <app-name>
pm2 restart <app-name>
pm2 stop <app-name>
pm2 delete <app-name>
```

### PM2 Ecosystem File (Optional)

```javascript
module.exports = {
  apps: [
    {
      name: '<app-name>',
      script: '<entry-file>',
      env: {
        PORT: <port>,
        NODE_ENV: 'production',
      },
      watch: false,
      max_restarts: 10,
      restart_delay: 3000,
    },
  ],
};
```

---

## Option 2: Docker

### Dockerfile

```dockerfile
FROM node:20-alpine

WORKDIR /app

# Install dependencies hệ thống nếu cần
# RUN apk add --no-cache git

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE <port>

CMD ["node", "<entry-file>"]
```

### Build & Run

```bash
docker build -t <app-name> .
docker run -d \
  --name <app-name> \
  -p <port>:<port> \
  -v /path/to/data:/data:ro \
  <app-name>
```

### Docker Compose

```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - '<port>:<port>'
    volumes:
      - ./config:/app/config
    restart: unless-stopped
    environment:
      - PORT=<port>
```

---

## Option 3: Nginx Reverse Proxy

### Nginx Config

```nginx
server {
    listen 80;
    server_name <domain>;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name <domain>;

    ssl_certificate /etc/letsencrypt/live/<domain>/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/<domain>/privkey.pem;

    # WebSocket support (nếu có)
    location /ws {
        proxy_pass http://localhost:<port>;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    location / {
        proxy_pass http://localhost:<port>;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### HTTPS with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d <domain>
```

---

## Security Considerations

### Access Control

1. **Restrict by IP** trong Nginx
2. **HTTP Basic Auth** với Nginx
3. Secrets lưu trong `.env`, không commit

### Repository/Data Access

- Chỉ dùng read-only commands
- Mount directories read-only trong Docker (`:ro`)

---

## Environment Variables

| Variable | Default  | Description      |
| -------- | -------- | ---------------- |
| `PORT`   | `<port>` | HTTP server port |

---

## Health Check

```bash
curl http://localhost:<port>/api/health
# Expected: {"status":"ok"}
```
