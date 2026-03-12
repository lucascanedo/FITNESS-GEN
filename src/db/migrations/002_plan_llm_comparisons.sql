-- Migration: dedicated comparison table between LLM plan and teacher-edited plan

CREATE TABLE IF NOT EXISTS plan_llm_comparisons (
    id BIGSERIAL PRIMARY KEY,
    plan_id INT NOT NULL UNIQUE REFERENCES plans(id) ON DELETE CASCADE,
    llm_plan_json JSONB NOT NULL,
    edited_plan_json JSONB NOT NULL,
    similarity_score NUMERIC(6,4) NOT NULL DEFAULT 1.0,
    comparison_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_plan_llm_comparisons_similarity
ON plan_llm_comparisons(similarity_score);

CREATE INDEX IF NOT EXISTS idx_plan_llm_comparisons_updated
ON plan_llm_comparisons(updated_at DESC);

INSERT INTO plan_llm_comparisons (
    plan_id,
    llm_plan_json,
    edited_plan_json,
    similarity_score,
    comparison_json
)
SELECT
    p.id,
    COALESCE(p.generated_plan_json, p.plan_json),
    p.plan_json,
    CASE
        WHEN COALESCE(p.generated_plan_json, p.plan_json) = p.plan_json THEN 1.0
        ELSE 0.0
    END,
    jsonb_build_object(
        'summary',
        jsonb_build_object(
            'backfilled', true,
            'original_split', COALESCE(p.generated_plan_json->'plan_meta'->>'split', p.plan_json->'plan_meta'->>'split'),
            'final_split', p.plan_json->'plan_meta'->>'split'
        )
    )
FROM plans p
WHERE p.plan_json IS NOT NULL
ON CONFLICT (plan_id) DO NOTHING;
