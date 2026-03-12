# src/IA/llm_helpers.py
from typing import Any, Dict

from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.repositories import llm_repository


def get_llm_bundle(
    db: Session,
    student_id: int,
    assessment_id: int,
    measurement_id: int,
    enforce_snapshot_match: bool = False,
) -> Dict[str, Any]:
    row = llm_repository.select_llm_bundle_row(db, student_id, assessment_id, measurement_id)
    if row is None:
        raise HTTPException(status_code=404, detail="IDs invÃ¡lidos ou incoerentes (student/assessment/measurement).")

    if row["a_student_id"] != student_id:
        raise HTTPException(status_code=400, detail="assessment_id nÃ£o pertence ao student_id informado.")
    if row["m_student_id"] != student_id:
        raise HTTPException(status_code=400, detail="measurement_id nÃ£o pertence ao student_id informado.")

    if enforce_snapshot_match and row["assessment_snapshot_mid"] is not None:
        if row["assessment_snapshot_mid"] != measurement_id:
            raise HTTPException(
                status_code=400,
                detail="measurement_id difere do snapshot salvo em assessments.measurement_id."
            )

    return {
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
            "status": row["status"],
        },
        "measurement": {
            "height_m": row["height_m"],
            "weight_kg": row["weight_kg"],
            "body_fat_percent": row["body_fat_percent"],
            "muscle_mass_kg": row["muscle_mass_kg"],
            "bmi": row["bmi"],
            "source": row["measurement_source"],
            "notes": row["measurement_notes"],
        },
    }
