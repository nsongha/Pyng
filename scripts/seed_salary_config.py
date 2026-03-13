"""Seed salary config vào Supabase system_config table.

Usage:
    python3 scripts/seed_salary_config.py

Requires: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY trong .env
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from db import client as db


SALARY_CONFIGS = [
    {"key": "salary_basic_monthly", "value": "10000000", "description": "Lương cơ bản/tháng (VND)"},
    {"key": "salary_ot_rate_per_hour", "value": "50000", "description": "OT rate/giờ (VND)"},
    {"key": "salary_late_deduction_per_min", "value": "5000", "description": "Trừ lương/phút đi muộn (VND)"},
    {"key": "salary_late_grace_minutes", "value": "5", "description": "Grace period đi muộn (phút)"},
]


def seed():
    for config in SALARY_CONFIGS:
        # Upsert: update if exists, insert if not
        existing = db.select(
            "system_config",
            filters={"key": config["key"]},
            limit=1,
        )

        if existing:
            print(f"⚠️  {config['key']} đã tồn tại = {existing[0].get('value')}, skip")
        else:
            db.insert("system_config", {
                "key": config["key"],
                "value": config["value"],
            })
            print(f"✅ Seeded {config['key']} = {config['value']}")

    print("\n🎉 Done! Salary config seeded.")


if __name__ == "__main__":
    seed()
