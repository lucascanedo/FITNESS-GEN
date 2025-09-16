# src/ai/llm_helper.py
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException


def get_llm_bundle(
    db: Session,
    student_id: int,
    assessment_id: int,
    measurement_id: int,
    enforce_snapshot_match: bool = False,
) -> Dict[str, Any]:
    """
    Valida os 3 IDs e retorna um 'bundle' com:
      - student: id, name, sex, age
      - assessment: TODOS os campos relevantes (ver esquema)
      - measurement: TODOS os campos relevantes (ver esquema)

    Exige:
      - assessments.student_id == student_id
      - measurements.student_id == student_id
      - (opcional) assessments.measurement_id == measurement_id  (snapshot)
    """

    # 1) Busca + valida pertença numa consulta compacta
    stmt = text("""
        SELECT
            -- student
            s.id   AS student_id,
            s.name AS student_name,
            s.sex  AS student_sex,
            s.age  AS student_age,

            -- assessment
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

            -- measurement (selecionada)
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
    """)

    row = db.execute(stmt, {"sid": student_id, "aid": assessment_id, "mid": measurement_id}).mappings().one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="IDs inválidos ou incoerentes (student/assessment/measurement).")

    # 2) Checagens adicionais de pertença
    if row["a_student_id"] != student_id:
        raise HTTPException(status_code=400, detail="assessment_id não pertence ao student_id informado.")
    if row["m_student_id"] != student_id:
        raise HTTPException(status_code=400, detail="measurement_id não pertence ao student_id informado.")

    # 3) (Opcional) Enforcar snapshot salvo no assessment
    if enforce_snapshot_match and row["assessment_snapshot_mid"] is not None:
        if row["assessment_snapshot_mid"] != measurement_id:
            raise HTTPException(
                status_code=400,
                detail="measurement_id difere do snapshot salvo em assessments.measurement_id."
            )

    # 4) Monta bundle limpo para o LLM
    bundle: Dict[str, Any] = {
        "student": {
            "id": row["student_id"],
            "name": row["student_name"],
            "sex": row["student_sex"],
            "age": row["student_age"],
        },
        "assessment": {
            "id": row["assessment_id"],
            "objectives": row["objectives"],
            "posture": row["posture"],
            "injuries": row["injuries"],
            "restrictions": row["restrictions"],
            "history": row["history"],
            "level": row["level"],
            "freq_per_week": row["freq_per_week"],
            "session_time_min": row["session_time_min"],
            "case_notes": row["case_notes"],
            "equipment": row["equipment"],
            "red_flags": row["red_flags"],
            "readiness": row["readiness"],
            "periodization": row["periodization"],
            "status": row["status"]
        },
        "measurement": {
            "height_m": row["height_m"],
            "weight_kg": row["weight_kg"],
            "body_fat_percent": row["body_fat_percent"],
            "muscle_mass_kg": row["muscle_mass_kg"],
            "bmi": row["bmi"],
            "source": row["measurement_source"],
            "notes": row["measurement_notes"]
        },
    }
    return bundle
