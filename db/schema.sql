-- ============================================================
-- Pyng — Database Schema
-- Chạy trên Supabase SQL Editor (https://supabase.com/dashboard)
-- Source of truth: docs/ARCHITECTURE.md §2
-- Seed data: docs/DEPLOYMENT.md §4
-- ============================================================
-- ==========================================
-- 1. Users
-- ==========================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    telegram_username VARCHAR(100),
    full_name VARCHAR(200) NOT NULL,
    email VARCHAR(200) UNIQUE,
    role VARCHAR(20) DEFAULT 'employee',
    -- employee | manager | admin
    department VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    registered_at TIMESTAMP DEFAULT NOW(),
    face_photo_url VARCHAR(500),
    -- optional, Face++ enrolled
    annual_leave_days INT DEFAULT 12
);
-- ==========================================
-- 2. Offices
-- ==========================================
CREATE TABLE offices (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    radius_m INT DEFAULT 100,
    is_active BOOLEAN DEFAULT TRUE,
    created_by BIGINT REFERENCES users(telegram_id),
    created_at TIMESTAMP DEFAULT NOW()
);
-- ==========================================
-- 3. WiFi Whitelist
-- ==========================================
CREATE TABLE wifi_whitelist (
    id SERIAL PRIMARY KEY,
    office_id INT REFERENCES offices(id),
    ssid VARCHAR(200) NOT NULL,
    description VARCHAR(200),
    is_active BOOLEAN DEFAULT TRUE,
    added_by BIGINT REFERENCES users(telegram_id),
    added_at TIMESTAMP DEFAULT NOW()
);
-- ==========================================
-- 4. NFC Tokens
-- ==========================================
CREATE TABLE nfc_tokens (
    id SERIAL PRIMARY KEY,
    token VARCHAR(100) UNIQUE NOT NULL,
    office_id INT REFERENCES offices(id),
    location VARCHAR(200),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
-- ==========================================
-- 5. QR Sessions
-- ==========================================
CREATE TABLE qr_sessions (
    id SERIAL PRIMARY KEY,
    token VARCHAR(100) UNIQUE NOT NULL,
    office_id INT REFERENCES offices(id),
    created_at TIMESTAMP DEFAULT NOW(),
    expire_at TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT FALSE
);
CREATE INDEX idx_qr_expire ON qr_sessions(expire_at);
-- ==========================================
-- 6. Check-ins
-- ==========================================
CREATE TABLE checkins (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    type VARCHAR(10) NOT NULL,
    -- 'in' | 'out'
    method VARCHAR(20) NOT NULL,
    -- 'gps' | 'wifi' | 'qr' | 'nfc' | 'manual'
    office_id INT REFERENCES offices(id),
    -- GPS fields
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    gps_accuracy_m INT,
    distance_m INT,
    -- Meta
    wifi_ssid VARCHAR(200),
    is_valid BOOLEAN DEFAULT TRUE,
    is_manual_approved BOOLEAN,
    approved_by BIGINT,
    -- Mood
    mood VARCHAR(20),
    -- 'great' | 'good' | 'tired' | 'sos'
    note TEXT,
    -- Timestamps
    checked_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_checkins_user_date ON checkins(user_id, checked_at);
CREATE INDEX idx_checkins_date ON checkins(checked_at);
-- ==========================================
-- 7. Leaves
-- ==========================================
CREATE TABLE leaves (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    leave_type VARCHAR(30) NOT NULL,
    -- 'annual' | 'compensatory' | 'unpaid' | 'sick'
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    days_count DECIMAL(4, 1),
    reason TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    approved_by INT REFERENCES users(id),
    requested_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP
);
-- ==========================================
-- 8. Gamification
-- ==========================================
CREATE TABLE gamification (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) UNIQUE,
    total_points INT DEFAULT 0,
    current_streak INT DEFAULT 0,
    longest_streak INT DEFAULT 0,
    ontime_count INT DEFAULT 0,
    early_count INT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW()
);
-- ==========================================
-- 9. Point Transactions
-- ==========================================
CREATE TABLE point_transactions (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    points INT NOT NULL,
    reason VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);
-- ==========================================
-- 10. System Config
-- ==========================================
CREATE TABLE system_config (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    updated_by BIGINT,
    updated_at TIMESTAMP DEFAULT NOW()
);
-- ==========================================
-- Enable RLS on all tables
-- ==========================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE offices ENABLE ROW LEVEL SECURITY;
ALTER TABLE wifi_whitelist ENABLE ROW LEVEL SECURITY;
ALTER TABLE nfc_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE qr_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE checkins ENABLE ROW LEVEL SECURITY;
ALTER TABLE leaves ENABLE ROW LEVEL SECURITY;
ALTER TABLE gamification ENABLE ROW LEVEL SECURITY;
ALTER TABLE point_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_config ENABLE ROW LEVEL SECURITY;