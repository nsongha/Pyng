---
description: Python code style, formatting, imports
---

# Code Style

## Python Style

- Follow PEP 8
- Line length: 88 characters (Black formatter default)
- Indentation: 4 spaces
- Quotes: double quotes `"` preferred

## Imports

- Thứ tự: stdlib → third-party → local
- Mỗi group cách nhau 1 dòng trống
- KHÔNG import wildcard: `from module import *`

```python
import os
import json
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from config.settings import TELEGRAM_BOT_TOKEN
from services.checkin import CheckinService
```

## Docstrings

- Mọi module: docstring ở đầu file mô tả mục đích
- Functions phức tạp: docstring mô tả params, returns
- Format: Google style docstrings

```python
def validate_location(lat: float, lng: float, office_id: int) -> bool:
    """Kiểm tra vị trí có nằm trong geofence của office.

    Args:
        lat: Vĩ độ GPS
        lng: Kinh độ GPS
        office_id: ID văn phòng cần kiểm tra

    Returns:
        True nếu vị trí hợp lệ, False nếu ngoài geofence
    """
```

## Type Hints

- LUÔN dùng type hints cho function parameters và return types
- Dùng `Optional[X]` thay vì `X | None` (cho Python 3.9 compat)
- Dùng `from __future__ import annotations` nếu cần forward refs
