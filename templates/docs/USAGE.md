# [Tên Dự Án] — User Guide

## Prerequisites

- **Node.js** 18+ (LTS recommended)
- **[Dependency khác]** installed and accessible in PATH
- [Yêu cầu khác]

## Installation

```bash
# 1. Clone repository
git clone https://github.com/<org>/<repo>.git
cd <repo>

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev
```

App sẽ khả dụng tại **http://localhost:[PORT]**

## Getting Started

<!-- Hướng dẫn bước đầu tiên cho user mới -->

1. Mở app trong browser
2. [Bước tiếp theo]
3. [Bước tiếp theo]

> 💡 [Tip hữu ích cho user mới]

## Configuration

### [Config Section 1]

| Field        | Description |
| ------------ | ----------- |
| [field name] | [mô tả]     |
| [field name] | [mô tả]     |

### [Config Section 2]

| Field        | Description |
| ------------ | ----------- |
| [field name] | [mô tả]     |

## Features Overview

### [Feature Category 1]

| Feature        | Description |
| -------------- | ----------- |
| [feature name] | [mô tả]     |
| [feature name] | [mô tả]     |

### [Feature Category 2]

| Feature        | Description |
| -------------- | ----------- |
| [feature name] | [mô tả]     |

### Keyboard Shortcuts

| Shortcut        | Action   |
| --------------- | -------- |
| `⌘K` / `Ctrl+K` | [action] |
| `Escape`        | [action] |

## Cấu hình: config và environment

### config.json — Non-sensitive settings

```json
{
  "key": "value"
}
```

### .env — Secrets (không bao giờ commit)

```bash
# Copy từ template rồi điền giá trị thật
cp .env.example .env
```

```env
API_KEY=your_api_key
SECRET=your_secret
```

> ⚠️ **Không bao giờ commit `.env`**. File `.env.example` (không có giá trị thật) mới được commit làm template.
