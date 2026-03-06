-- Migration: Plan versioning and AI learning support
-- Run this on existing databases to add new tables/columns.

-- 1) Add missing columns to assessments (if not exist)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'assessments' AND column_name = 'case_notes') THEN
        ALTER TABLE assessments ADD COLUMN case_notes TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'assessments' AND column_name = 'equipment') THEN
        ALTER TABLE assessments ADD COLUMN equipment JSONB;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'assessments' AND column_name = 'red_flags') THEN
        ALTER TABLE assessments ADD COLUMN red_flags JSONB;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'assessments' AND column_name = 'readiness') THEN
        ALTER TABLE assessments ADD COLUMN readiness JSONB;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'assessments' AND column_name = 'periodization') THEN
        ALTER TABLE assessments ADD COLUMN periodization JSONB;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'assessments' AND column_name = 'status') THEN
        ALTER TABLE assessments ADD COLUMN status VARCHAR(20);
    END IF;
END $$;

-- 2) Create llm_calls table (if not exists)
-- plan_id is INT without FK to avoid circular dependency with plans.llm_call_id
CREATE TABLE IF NOT EXISTS llm_calls (
    id BIGSERIAL PRIMARY KEY,
    correlation_id VARCHAR(64),
    route VARCHAR(128),
    provider VARCHAR(32),
    model VARCHAR(128),
    prompt_hash VARCHAR(32),
    prompt_len INT,
    resp_len INT,
    duration_ms NUMERIC(10,2),
    error TEXT,
    resp_raw TEXT,
    student_id INT REFERENCES students(id) ON DELETE SET NULL,
    assessment_id INT REFERENCES assessments(id) ON DELETE SET NULL,
    measurement_id INT REFERENCES measurements(id) ON DELETE SET NULL,
    plan_id INT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_llm_calls_student ON llm_calls(student_id);
CREATE INDEX IF NOT EXISTS idx_llm_calls_correlation ON llm_calls(correlation_id);

-- 3) Add new columns to plans (run in order; handle existing data)
-- For plans that only have plan_json, we'll treat it as both generated and final
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'plans' AND column_name = 'generated_plan_json') THEN
        ALTER TABLE plans ADD COLUMN generated_plan_json JSONB;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'plans' AND column_name = 'llm_call_id') THEN
        ALTER TABLE plans ADD COLUMN llm_call_id BIGINT REFERENCES llm_calls(id) ON DELETE SET NULL;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'plans' AND column_name = 'edit_count') THEN
        ALTER TABLE plans ADD COLUMN edit_count INT DEFAULT 0;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'plans' AND column_name = 'updated_at') THEN
        ALTER TABLE plans ADD COLUMN updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- Migrate existing plans: plan_json becomes both generated_plan_json and plan_json
-- (only for plans that don't have generated_plan_json yet)
UPDATE plans SET generated_plan_json = plan_json WHERE generated_plan_json IS NULL AND plan_json IS NOT NULL;

-- Add NOT NULL to plan_json if we need to rename - plans already has plan_json NOT NULL
-- The new design: generated_plan_json (nullable), plan_json (not null)
-- Existing plans keep plan_json; we just add generated_plan_json = plan_json for them.

-- 4) Create plan_versions table
CREATE TABLE IF NOT EXISTS plan_versions (
    id BIGSERIAL PRIMARY KEY,
    plan_id INT NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
    version_number INT NOT NULL,
    source VARCHAR(20) NOT NULL CHECK (source IN ('llm', 'teacher')),
    plan_json JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(plan_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_plan_versions_plan ON plan_versions(plan_id);
