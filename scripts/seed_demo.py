"""Seed script — Tạo data 2 tháng (Feb + Mar 2026) cho user_id=1.

Chạy: python3 scripts/seed_demo.py

Data tạo:
- ~40 ngày check-in (in+out) với giờ realistic
- Mix methods: wifi, gps, qr, nfc, wfh
- Mix moods: great, good, tired, sos
- Gamification: tổng ~22 ngày ontime, streak dài nhất 8 ngày
- 2 leaves: 1 approved (2 ngày), 1 pending (1 ngày)
- Point transactions matching gamification
"""

import os
import sys
import random
from datetime import date, datetime, timedelta

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import client as db

USER_ID = 1
TZ_OFFSET = timedelta(hours=7)  # Asia/Ho_Chi_Minh = UTC+7

METHODS = ["wifi", "gps", "qr", "nfc", "wfh"]
MOODS = ["great", "good", "good", "tired", "sos"]  # weighted: good more common

# Ngày không đi làm — cuối tuần tự skip, thêm vài ngày nghỉ
HOLIDAYS = {
    date(2026, 2, 16),  # Tết
    date(2026, 2, 17),  # Tết
    date(2026, 2, 18),  # Tết
    date(2026, 2, 19),  # Tết
    date(2026, 2, 20),  # Tết
}

# Ngày nghỉ phép (skip checkin)
LEAVE_DAYS = {
    date(2026, 2, 23),  # Nghỉ phép (approved)
    date(2026, 2, 24),  # Nghỉ phép (approved)
    date(2026, 3, 5),   # Nghỉ ốm (approved)
}

# Ngày đã có data (skip)
EXISTING_DAYS = {
    date(2026, 3, 11),  # Đã có checkin thật
    date(2026, 3, 12),  # Hôm nay
}


def random_checkin_time(d: date, late_prob: float = 0.15) -> datetime:
    """Tạo giờ check-in realistic.
    
    ~85% ontime (8:00-8:59), ~15% late (9:00-9:30).
    """
    is_late = random.random() < late_prob
    if is_late:
        hour = 9
        minute = random.randint(0, 30)
    else:
        # Sớm: 7:30-7:59 (20%), đúng giờ: 8:00-8:50 (65%)
        r = random.random()
        if r < 0.2:
            hour = 7
            minute = random.randint(30, 59)
        else:
            hour = 8
            minute = random.randint(0, 50)
    
    return datetime(d.year, d.month, d.day, hour, minute, random.randint(0, 59))


def random_checkout_time(checkin_dt: datetime) -> datetime:
    """Tạo giờ checkout: ~8-9 giờ sau checkin."""
    hours = random.uniform(8.0, 10.0)
    return checkin_dt + timedelta(hours=hours)


def main():
    print("🌱 Bắt đầu seed data 2 tháng...")
    
    # Date range: Feb 1 - Mar 12, 2026
    start_date = date(2026, 2, 1)
    end_date = date(2026, 3, 12)
    
    checkins_created = 0
    current = start_date
    
    while current <= end_date:
        # Skip weekends
        if current.weekday() >= 5:  # Sat, Sun
            current += timedelta(days=1)
            continue
        
        # Skip holidays
        if current in HOLIDAYS:
            current += timedelta(days=1)
            continue
        
        # Skip leave days
        if current in LEAVE_DAYS:
            current += timedelta(days=1)
            continue
        
        # Skip existing data days
        if current in EXISTING_DAYS:
            current += timedelta(days=1)
            continue
        
        # Random method
        if current.weekday() == 4 and random.random() < 0.3:
            method = "wfh"  # Friday WFH 30%
        else:
            method = random.choice(["wifi", "gps", "qr", "nfc"])
        
        mood = random.choice(MOODS)
        
        # Check-in time (UTC = local - 7h)
        checkin_local = random_checkin_time(current, late_prob=0.15)
        checkin_utc = checkin_local - TZ_OFFSET
        
        checkout_local = random_checkout_time(checkin_local)
        checkout_utc = checkout_local - TZ_OFFSET
        
        # Insert check-in
        db.insert("checkins", {
            "user_id": USER_ID,
            "type": "in",
            "method": method,
            "is_valid": True,
            "mood": mood,
            "checked_at": checkin_utc.isoformat(),
            "created_at": checkin_utc.isoformat(),
        })
        
        # Insert check-out
        db.insert("checkins", {
            "user_id": USER_ID,
            "type": "out",
            "method": method,
            "is_valid": True,
            "checked_at": checkout_utc.isoformat(),
            "created_at": checkout_utc.isoformat(),
        })
        
        checkins_created += 1
        day_str = current.strftime("%a %d/%m")
        in_str = checkin_local.strftime("%H:%M")
        out_str = checkout_local.strftime("%H:%M")
        status = "🔴 late" if checkin_local.hour >= 9 else "🟢 ontime"
        print(f"  {day_str}: {in_str}-{out_str} ({method}) {status}")
        
        current += timedelta(days=1)
    
    print(f"\n✅ Tạo {checkins_created} ngày check-in (x2 records = {checkins_created * 2})")
    
    # --- Leaves ---
    print("\n📋 Tạo leave requests...")
    
    # Leave 1: Annual (approved) — Feb 23-24
    db.insert("leaves", {
        "user_id": USER_ID,
        "leave_type": "annual",
        "start_date": "2026-02-23",
        "end_date": "2026-02-24",
        "days_count": 2,
        "reason": "Việc gia đình",
        "status": "approved",
        "requested_at": "2026-02-20T03:00:00",
        "processed_at": "2026-02-20T05:00:00",
    })
    print("  ✅ Annual leave 23-24/02 (approved, 2 days)")
    
    # Leave 2: Sick (approved) — Mar 5
    db.insert("leaves", {
        "user_id": USER_ID,
        "leave_type": "sick",
        "start_date": "2026-03-05",
        "end_date": "2026-03-05",
        "days_count": 1,
        "reason": "Không khỏe",
        "status": "approved",
        "requested_at": "2026-03-05T01:00:00",
        "processed_at": "2026-03-05T02:00:00",
    })
    print("  ✅ Sick leave 05/03 (approved, 1 day)")
    
    # --- Update Gamification ---
    print("\n🏆 Update gamification stats...")
    
    # Tính lại ontime/late count
    ontime_count = int(checkins_created * 0.85)
    early_count = int(checkins_created * 0.20)
    
    db.update("gamification", {
        "total_points": checkins_created * 10 + ontime_count * 5 + early_count * 3,
        "current_streak": 7,  # 7 ngày liên tục gần đây
        "longest_streak": 12,
        "ontime_count": ontime_count,
        "early_count": early_count,
    }, filters={"user_id": USER_ID})
    print(f"  ✅ Points: {checkins_created * 10 + ontime_count * 5 + early_count * 3}, Streak: 7/12, Ontime: {ontime_count}")
    
    print("\n🎉 Seed hoàn tất!")


if __name__ == "__main__":
    main()
