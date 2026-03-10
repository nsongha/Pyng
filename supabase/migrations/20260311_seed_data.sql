-- Seed data BSMlabs
-- 1. System config
INSERT INTO system_config (key, value, updated_by, updated_at)
VALUES (
        'office_name',
        'BSMlabs Office',
        NULL,
        NOW()
    ),
    (
        'office_address',
        '219 Trung Kính, Yên Hòa, Cầu Giấy, Hà Nội',
        NULL,
        NOW()
    ),
    (
        'timezone',
        'Asia/Ho_Chi_Minh',
        NULL,
        NOW()
    ),
    (
        'work_start_time',
        '08:45',
        NULL,
        NOW()
    ),
    (
        'work_end_time',
        '17:45',
        NULL,
        NOW()
    ),
    (
        'checkin_remind_time',
        '08:30',
        NULL,
        NOW()
    ),
    (
        'checkout_remind_time',
        '17:45',
        NULL,
        NOW()
    ),
    (
        'daily_report_time',
        '09:15',
        NULL,
        NOW()
    ),
    (
        'late_budget_minutes',
        '180',
        NULL,
        NOW()
    ),
    (
        'late_grace_minutes',
        '5',
        NULL,
        NOW()
    ),
    (
        'wfh_limit_per_month',
        '2',
        NULL,
        NOW()
    ),
    (
        'qr_expire_seconds',
        '300',
        NULL,
        NOW()
    ),
    (
        'auto_checkout_time',
        '23:59',
        NULL,
        NOW()
    );
-- 2. Office + WiFi (dùng CTE để đảm bảo thứ tự)
WITH new_office AS (
    INSERT INTO offices (name, latitude, longitude, radius_m)
    VALUES (
            'BSMlabs — 219 Trung Kính',
            21.0285,
            105.7968,
            120
        )
    RETURNING id
)
INSERT INTO wifi_whitelist (office_id, ssid, description)
SELECT id,
    ssid,
    description
FROM new_office
    CROSS JOIN (
        VALUES ('BSMlabs_WiFi', 'WiFi chính văn phòng'),
            ('BSMlabs_5G', 'WiFi 5GHz văn phòng')
    ) AS w(ssid, description);