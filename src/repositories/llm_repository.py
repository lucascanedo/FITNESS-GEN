from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


def select_llm_bundle_row(
    db: Session,
    student_id: int,
    assessment_id: int,
    measurement_id: int,
):
    return db.execute(
        text("""
            SELECT
                s.id   AS student_id,
                s.name AS student_name,
                s.sex  AS student_sex,
                s.age  AS student_age,

                a.id                 AS assessment_id,
                a.student_id         AS a_student_id,
                a.measurement_id     AS assessment_snapshot_mid,
                a.objectives,
                a.posture,
                a.injuries,
                a.restrictions,
                a.history,
                a.level,
                a.freq_per_week,
                a.session_time_min,
                a.created_at         AS assessment_created_at,
                a.case_notes,
                a.equipment,
                a.red_flags,
                a.readiness,
                a.periodization,
                a.status,

                m.id                 AS measurement_id,
                m.student_id         AS m_student_id,
                m.measured_at,
                m.height_m,
                m.weight_kg,
                m.body_fat_percent,
                m.muscle_mass_kg,
                m.bmi,
                m.source             AS measurement_source,
                m.notes              AS measurement_notes,
                m.created_at         AS measurement_created_at
            FROM assessments a
            JOIN students s
              ON s.id = a.student_id
            JOIN measurements m
              ON m.id = :mid
             AND m.student_id = s.id
            WHERE a.id = :aid
              AND s.id = :sid;
        """),
        {"sid": student_id, "aid": assessment_id, "mid": measurement_id},
    ).mappings().one_or_none()
