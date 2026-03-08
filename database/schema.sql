-- =============================================================================
-- 2Care.ai Voice AI Agent - Database Schema
-- PostgreSQL 14+
-- =============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search

-- =============================================================================
-- PATIENTS TABLE
-- =============================================================================
CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(255),
    date_of_birth DATE,
    gender VARCHAR(20) CHECK (gender IN ('male', 'female', 'other')),
    preferred_language VARCHAR(10) DEFAULT 'en' CHECK (preferred_language IN ('en', 'hi', 'ta')),
    address TEXT,
    medical_record_number VARCHAR(50) UNIQUE,
    emergency_contact_name VARCHAR(255),
    emergency_contact_phone VARCHAR(20),
    insurance_provider VARCHAR(255),
    insurance_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_patients_phone ON patients(phone_number);
CREATE INDEX idx_patients_name ON patients USING gin(full_name gin_trgm_ops);

-- =============================================================================
-- DOCTORS TABLE
-- =============================================================================
CREATE TABLE doctors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(255) NOT NULL,
    specialty VARCHAR(100) NOT NULL,
    department VARCHAR(100),
    qualification VARCHAR(255),
    experience_years INTEGER,
    languages VARCHAR(10)[] DEFAULT ARRAY['en'],
    phone_number VARCHAR(20),
    email VARCHAR(255),
    consultation_fee INTEGER,
    is_active BOOLEAN DEFAULT true,
    bio TEXT,
    profile_image_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_doctors_specialty ON doctors(specialty);
CREATE INDEX idx_doctors_active ON doctors(is_active);

-- =============================================================================
-- DOCTOR SCHEDULES
-- =============================================================================
CREATE TABLE doctor_schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doctor_id UUID NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    slot_duration_minutes INTEGER DEFAULT 30,
    max_patients_per_slot INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    UNIQUE(doctor_id, day_of_week, start_time)
);

CREATE INDEX idx_schedules_doctor ON doctor_schedules(doctor_id);

-- =============================================================================
-- APPOINTMENTS TABLE
-- =============================================================================
CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL REFERENCES patients(id),
    doctor_id UUID NOT NULL REFERENCES doctors(id),
    appointment_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    appointment_type VARCHAR(50) DEFAULT 'consultation' 
        CHECK (appointment_type IN ('consultation', 'follow_up', 'checkup', 'emergency', 'telemedicine')),
    reason TEXT,
    status VARCHAR(20) DEFAULT 'scheduled' 
        CHECK (status IN ('scheduled', 'confirmed', 'completed', 'cancelled', 'no_show', 'rescheduled')),
    notes TEXT,
    reminder_sent BOOLEAN DEFAULT false,
    reminder_sent_at TIMESTAMP,
    booked_via VARCHAR(50) DEFAULT 'voice_ai',
    booking_session_id VARCHAR(100),
    previous_appointment_id UUID REFERENCES appointments(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_appointments_patient ON appointments(patient_id);
CREATE INDEX idx_appointments_doctor ON appointments(doctor_id);
CREATE INDEX idx_appointments_date ON appointments(appointment_date);
CREATE INDEX idx_appointments_status ON appointments(status);
CREATE INDEX idx_appointments_doctor_date ON appointments(doctor_id, appointment_date);

-- =============================================================================
-- CALL LOGS TABLE
-- =============================================================================
CREATE TABLE call_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(100) UNIQUE NOT NULL,
    patient_id UUID REFERENCES patients(id),
    phone_number VARCHAR(20),
    call_direction VARCHAR(20) DEFAULT 'inbound' CHECK (call_direction IN ('inbound', 'outbound')),
    call_start_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    call_end_time TIMESTAMP,
    duration_seconds INTEGER,
    language_used VARCHAR(10),
    languages_detected VARCHAR(10)[] DEFAULT ARRAY[]::VARCHAR[],
    intent_detected VARCHAR(100),
    outcome VARCHAR(50) CHECK (outcome IN ('appointment_booked', 'appointment_cancelled', 'appointment_rescheduled', 'inquiry_answered', 'escalated', 'abandoned', 'completed')),
    appointment_id UUID REFERENCES appointments(id),
    transcript TEXT,
    sentiment_score SMALLINT CHECK (sentiment_score BETWEEN -100 AND 100),
    escalated_to_human BOOLEAN DEFAULT false,
    escalation_reason TEXT,
    total_turns INTEGER DEFAULT 0,
    avg_latency_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_call_logs_session ON call_logs(session_id);
CREATE INDEX idx_call_logs_patient ON call_logs(patient_id);
CREATE INDEX idx_call_logs_date ON call_logs(call_start_time);

-- =============================================================================
-- CONVERSATION TURNS TABLE
-- =============================================================================
CREATE TABLE conversation_turns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_log_id UUID NOT NULL REFERENCES call_logs(id) ON DELETE CASCADE,
    turn_number INTEGER NOT NULL,
    speaker VARCHAR(20) NOT NULL CHECK (speaker IN ('user', 'agent')),
    text TEXT NOT NULL,
    audio_url VARCHAR(500),
    language VARCHAR(10),
    intent VARCHAR(100),
    slots JSONB,
    confidence SMALLINT CHECK (confidence BETWEEN 0 AND 100),
    stt_latency_ms INTEGER,
    llm_latency_ms INTEGER,
    tts_latency_ms INTEGER,
    total_latency_ms INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_turns_call ON conversation_turns(call_log_id);
CREATE INDEX idx_turns_intent ON conversation_turns(intent);

-- =============================================================================
-- CLINIC/HOSPITAL CONFIGURATION
-- =============================================================================
CREATE TABLE clinic_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clinic_name VARCHAR(255) NOT NULL,
    address TEXT,
    phone_number VARCHAR(20),
    email VARCHAR(255),
    working_hours JSONB,
    supported_languages VARCHAR(10)[] DEFAULT ARRAY['en', 'hi', 'ta'],
    appointment_duration_minutes INTEGER DEFAULT 30,
    advance_booking_days INTEGER DEFAULT 30,
    cancellation_policy TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- HOLIDAYS TABLE
-- =============================================================================
CREATE TABLE holidays (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    holiday_date DATE NOT NULL,
    name VARCHAR(255) NOT NULL,
    is_full_day BOOLEAN DEFAULT true,
    doctor_id UUID REFERENCES doctors(id),  -- NULL means applies to all
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_holidays_date ON holidays(holiday_date);

-- =============================================================================
-- OUTBOUND CAMPAIGNS
-- =============================================================================
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    campaign_type VARCHAR(50) CHECK (campaign_type IN ('reminder', 'follow_up', 'health_checkup', 'survey')),
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'scheduled', 'running', 'paused', 'completed')),
    scheduled_start TIMESTAMP,
    scheduled_end TIMESTAMP,
    target_count INTEGER DEFAULT 0,
    completed_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    script_template TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- CAMPAIGN TARGETS
-- =============================================================================
CREATE TABLE campaign_targets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    patient_id UUID NOT NULL REFERENCES patients(id),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'skipped')),
    call_log_id UUID REFERENCES call_logs(id),
    attempts INTEGER DEFAULT 0,
    last_attempt_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_campaign_targets ON campaign_targets(campaign_id, status);

-- =============================================================================
-- TRIGGERS FOR UPDATED_AT
-- =============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_patients_updated_at BEFORE UPDATE ON patients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_doctors_updated_at BEFORE UPDATE ON doctors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_appointments_updated_at BEFORE UPDATE ON appointments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_clinic_config_updated_at BEFORE UPDATE ON clinic_config
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_campaigns_updated_at BEFORE UPDATE ON campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- SAMPLE DATA
-- =============================================================================

-- Insert sample doctors
INSERT INTO doctors (id, full_name, specialty, department, qualification, experience_years, languages, consultation_fee) VALUES
    (uuid_generate_v4(), 'Dr. Priya Sharma', 'General Medicine', 'Internal Medicine', 'MBBS, MD', 15, ARRAY['en', 'hi'], 500),
    (uuid_generate_v4(), 'Dr. Rajesh Kumar', 'Cardiology', 'Cardiology', 'MBBS, DM Cardiology', 20, ARRAY['en', 'hi'], 1000),
    (uuid_generate_v4(), 'Dr. Lakshmi Sundaram', 'Pediatrics', 'Pediatrics', 'MBBS, DCH', 12, ARRAY['en', 'ta'], 600),
    (uuid_generate_v4(), 'Dr. Venkatesh Iyer', 'Orthopedics', 'Orthopedics', 'MBBS, MS Ortho', 18, ARRAY['en', 'hi', 'ta'], 800),
    (uuid_generate_v4(), 'Dr. Ananya Patel', 'Dermatology', 'Dermatology', 'MBBS, MD Dermatology', 8, ARRAY['en', 'hi'], 700);

-- Insert sample clinic config
INSERT INTO clinic_config (clinic_name, address, phone_number, working_hours) VALUES
    ('2Care.ai Medical Center', '123 Health Street, Medical District, Mumbai 400001', '+91-22-12345678', 
     '{"monday": {"open": "09:00", "close": "18:00"}, "tuesday": {"open": "09:00", "close": "18:00"}, "wednesday": {"open": "09:00", "close": "18:00"}, "thursday": {"open": "09:00", "close": "18:00"}, "friday": {"open": "09:00", "close": "18:00"}, "saturday": {"open": "09:00", "close": "14:00"}, "sunday": null}');

-- Insert sample schedules for doctors
INSERT INTO doctor_schedules (doctor_id, day_of_week, start_time, end_time, slot_duration_minutes)
SELECT d.id, day.n, '09:00'::TIME, '17:00'::TIME, 30
FROM doctors d
CROSS JOIN generate_series(0, 5) AS day(n);
