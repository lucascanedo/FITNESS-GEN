-- Migration: explicit current plan pointer per student and backfill

CREATE TABLE IF NOT EXISTS student_current_plans (
    student_id INT PRIMARY KEY REFERENCES students(id) ON DELETE CASCADE,
    plan_id INT NOT NULL UNIQUE REFERENCES plans(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_student_current_plans_plan
ON student_current_plans(plan_id);

INSERT INTO student_current_plans (student_id, plan_id, assigned_at, updated_at)
SELECT DISTINCT ON (p.student_id)
    p.student_id,
    p.id,
    COALESCE(p.updated_at, p.created_at, CURRENT_TIMESTAMP),
    COALESCE(p.updated_at, p.created_at, CURRENT_TIMESTAMP)
FROM plans p
ORDER BY p.student_id, COALESCE(p.updated_at, p.created_at, CURRENT_TIMESTAMP) DESC, p.id DESC
ON CONFLICT (student_id) DO UPDATE
SET
    plan_id = EXCLUDED.plan_id,
    assigned_at = EXCLUDED.assigned_at,
    updated_at = EXCLUDED.updated_at;
