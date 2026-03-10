"""Pyng — Cấu hình toàn cục từ environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()


# ==========================================
# Telegram
# ==========================================
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
BOT_USERNAME: str = os.getenv("BOT_USERNAME", "PyngBot")
WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")
WEBHOOK_PATH: str = os.getenv("WEBHOOK_PATH", "/api/webhook")

# ==========================================
# Database (Supabase)
# ==========================================
DATABASE_URL: str = os.getenv("DATABASE_URL", "")
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# ==========================================
# Office Config
# ==========================================
OFFICE_NAME: str = os.getenv("OFFICE_NAME", "BSMlabs Office")
OFFICE_LAT: float = float(os.getenv("OFFICE_LAT", "21.0285"))
OFFICE_LNG: float = float(os.getenv("OFFICE_LNG", "105.7968"))
DEFAULT_GEOFENCE_RADIUS_M: int = int(os.getenv("DEFAULT_GEOFENCE_RADIUS_M", "120"))

# ==========================================
# Work Schedule
# ==========================================
TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Ho_Chi_Minh")
WORK_START: str = os.getenv("WORK_START", "08:45")
WORK_END: str = os.getenv("WORK_END", "17:45")

# ==========================================
# Policy
# ==========================================
LATE_BUDGET_MINUTES: int = int(os.getenv("LATE_BUDGET_MINUTES", "180"))
LATE_GRACE_MINUTES: int = int(os.getenv("LATE_GRACE_MINUTES", "5"))
WFH_LIMIT_PER_MONTH: int = int(os.getenv("WFH_LIMIT_PER_MONTH", "2"))
QR_EXPIRE_SECONDS: int = int(os.getenv("QR_EXPIRE_SECONDS", "300"))

# ==========================================
# WiFi
# ==========================================
OFFICE_WIFI_SSIDS: list[str] = [
    x.strip() for x in os.getenv("OFFICE_WIFI_SSIDS", "").split(",") if x.strip()
]

# ==========================================
# Admin
# ==========================================
ADMIN_TELEGRAM_IDS: list[int] = [
    int(x.strip()) for x in os.getenv("ADMIN_TELEGRAM_IDS", "").split(",") if x.strip()
]
ADMIN_GROUP_ID: int = int(os.getenv("ADMIN_GROUP_ID", "0"))

# ==========================================
# Security
# ==========================================
CRON_SECRET: str = os.getenv("CRON_SECRET", "")
JWT_SECRET: str = os.getenv("JWT_SECRET", "")
JWT_EXPIRE_HOURS: int = int(os.getenv("JWT_EXPIRE_HOURS", "24"))

# ==========================================
# Mini App
# ==========================================
MINI_APP_URL: str = os.getenv("MINI_APP_URL", "")
QR_DISPLAY_URL: str = os.getenv("QR_DISPLAY_URL", "")
