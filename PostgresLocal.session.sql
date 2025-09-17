CREATE TABLE IF NOT EXISTS llm_calls (
  id BIGSERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT now(),
  correlation_id TEXT,
  route TEXT,
  provider TEXT,
  model TEXT,
  prompt_hash TEXT,
  prompt_len INT,
  resp_len INT,
  duration_ms NUMERIC,
  error TEXT,
  student_id INT,
  assessment_id INT,
  measurement_id INT
);
CREATE INDEX IF NOT EXISTS idx_llm_calls_correlation_id ON llm_calls(correlation_id);
CREATE INDEX IF NOT EXISTS idx_llm_calls_created_at ON llm_calls(created_at);
CREATE INDEX IF NOT EXISTS idx_llm_calls_student_id ON llm_calls(id);

