-- ========================
-- SCHEMA FITNESSGEN (PostgreSQL)
-- ========================

-- Você já está conectado no DB fitnessgen. Se precisar:
-- CREATE DATABASE fitnessgen;
-- \c fitnessgen

-- ========================
-- TABELA: STUDENTS
-- ========================
CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    birth_date DATE NOT NULL,
    age INT NOT NULL,
    sex VARCHAR(10),
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Funções/trigger para idade
CREATE OR REPLACE FUNCTION calculate_age(birth DATE)
RETURNS INT AS $$
BEGIN
    RETURN DATE_PART('year', AGE(CURRENT_DATE, birth));
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION set_student_age()
RETURNS TRIGGER AS $$
BEGIN
    NEW.age := calculate_age(NEW.birth_date);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_set_student_age ON students;
CREATE TRIGGER trg_set_student_age
BEFORE INSERT OR UPDATE ON students
FOR EACH ROW
EXECUTE FUNCTION set_student_age();

-- (Opcional) rotina diária para virar aniversários
CREATE OR REPLACE FUNCTION recalc_all_ages()
RETURNS void AS $$
BEGIN
    UPDATE students SET age = calculate_age(birth_date);
END;
$$ LANGUAGE plpgsql;

-- ========================
-- TABELA: MEASUREMENTS (histórico / append-only)
-- ========================
-- Limpa objetos antigos desta tabela (se existirem)
DROP TRIGGER IF EXISTS trg_compute_measurement_derivations ON measurements;
DROP FUNCTION IF EXISTS compute_measurement_derivations();
DROP TABLE IF EXISTS measurements CASCADE;

CREATE TABLE IF NOT EXISTS measurements (
    id SERIAL PRIMARY KEY,
    student_id INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    measured_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, -- quando a medida foi feita
    height_m DOUBLE PRECISION,
    weight_kg DOUBLE PRECISION,
    body_fat_percent DOUBLE PRECISION,
    muscle_mass_kg DOUBLE PRECISION,
    -- derivados
    bmi DOUBLE PRECISION,                 -- calculado via trigger
    -- metadados
    source TEXT,
    notes  TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Evita check-in duplicado no mesmo instante para o mesmo aluno
CREATE UNIQUE INDEX IF NOT EXISTS measurements_unique_checkin
ON measurements (student_id, measured_at);

-- Índice para histórico
CREATE INDEX IF NOT EXISTS idx_measurements_student_time
ON measurements (student_id, measured_at DESC);

-- Trigger: calcula BMI automaticamente
CREATE OR REPLACE FUNCTION compute_measurement_derivations()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.weight_kg IS NOT NULL AND NEW.height_m IS NOT NULL AND NEW.height_m > 0 THEN
        NEW.bmi := NEW.weight_kg / (NEW.height_m * NEW.height_m);
    ELSE
        NEW.bmi := NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_compute_measurement_derivations
BEFORE INSERT OR UPDATE ON measurements
FOR EACH ROW
EXECUTE FUNCTION compute_measurement_derivations();

-- ========================
-- TABELA: ASSESSMENTS (anamnese)
-- ========================
CREATE TABLE IF NOT EXISTS assessments (
    id SERIAL PRIMARY KEY,
    student_id INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    measurement_id INT REFERENCES measurements(id) ON DELETE SET NULL, -- snapshot opcional
    objectives JSONB,
    posture JSONB,
    injuries JSONB,
    restrictions JSONB,
    history JSONB,
    level VARCHAR(20),
    freq_per_week INT,
    session_time_min INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_assessments_student
ON assessments (student_id);

-- ========================
-- TABELA: PLANS (planos gerados pelo LLM)
-- ========================

CREATE TABLE IF NOT EXISTS plans (
    id SERIAL PRIMARY KEY,
    student_id INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    assessment_id INT NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    measurement_id INT REFERENCES measurements(id) ON DELETE SET NULL,
    plan_json JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_plans_student
ON plans (student_id);

CREATE INDEX IF NOT EXISTS idx_plans_assessment
ON plans (assessment_id);
