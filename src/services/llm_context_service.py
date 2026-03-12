from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session

from src.IA.llm_helpers import get_llm_bundle
from src.services.plan_analysis_service import build_llm_learning_context


def _sanitize_text(value: Any, limit: int = 280) -> str:
    if value is None:
        return ""
    text_value = str(value).replace("\r", " ").replace("\n", " ").strip()
    if not text_value:
        return ""
    sanitized = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[redacted-email]", text_value)
    sanitized = re.sub(r"\+?\d[\d\s\-\(\)]{7,}\d", "[redacted-number]", sanitized)
    return sanitized[:limit]


def sanitize_bundle_for_prompt(bundle: dict[str, Any]) -> dict[str, Any]:
    student = bundle.get("student") or {}
    assessment = bundle.get("assessment") or {}
    measurement = bundle.get("measurement") or {}

    return {
        "student": {
            "sex": student.get("sex"),
            "age": student.get("age"),
        },
        "assessment": {
            "objectives": assessment.get("objectives"),
            "posture": assessment.get("posture"),
            "injuries": assessment.get("injuries"),
            "restrictions": assessment.get("restrictions"),
            "history": _sanitize_text(assessment.get("history")),
            "level": assessment.get("level"),
            "freq_per_week": assessment.get("freq_per_week"),
            "session_time_min": assessment.get("session_time_min"),
            "case_notes": _sanitize_text(assessment.get("case_notes")),
            "equipment": assessment.get("equipment"),
            "red_flags": assessment.get("red_flags"),
            "readiness": assessment.get("readiness"),
            "periodization": assessment.get("periodization"),
            "status": assessment.get("status"),
        },
        "measurement": {
            "height_m": measurement.get("height_m"),
            "weight_kg": measurement.get("weight_kg"),
            "body_fat_percent": measurement.get("body_fat_percent"),
            "muscle_mass_kg": measurement.get("muscle_mass_kg"),
            "bmi": measurement.get("bmi"),
            "source": measurement.get("source"),
        },
    }


def build_generation_context(
    db: Session,
    student_id: int,
    assessment_id: int,
    measurement_id: int,
    include_learning: bool = True,
) -> dict[str, Any]:
    raw_bundle = get_llm_bundle(
        db=db,
        student_id=student_id,
        assessment_id=assessment_id,
        measurement_id=measurement_id,
        enforce_snapshot_match=False,
    )
    prompt_bundle = sanitize_bundle_for_prompt(raw_bundle)
    if include_learning:
        learning = build_llm_learning_context(db, target_bundle=raw_bundle)
        if learning:
            prompt_bundle["_learning_context"] = learning
    return prompt_bundle
