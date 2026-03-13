from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


JSON_FIELDS = (
    "objectives",
    "posture",
    "injuries",
    "restrictions",
    "history",
    "equipment",
    "red_flags",
    "readiness",
    "periodization",
)


def _prepare_assessment_data(data: dict[str, Any]) -> dict[str, Any]:
    prepared = dict(data)
    for field in JSON_FIELDS:
        value = prepared.get(field)
        if value is not None:
            prepared[field] = json.dumps(value)
    return prepared


def insert_assessment(db: Session, data: dict[str, Any]):
    prepared = _prepare_assessment_data(data)
    return db.execute(text("""
        INSERT INTO assessments (
            student_id, measurement_id, objectives, posture, injuries, restrictions,
            history, level, freq_per_week, session_time_min,
            case_notes, equipment, red_flags, readiness, periodization, status
        )
        VALUES (
            :student_id, :measurement_id, CAST(:objectives AS jsonb), CAST(:posture AS jsonb), CAST(:injuries AS jsonb), CAST(:restrictions AS jsonb),
            CAST(:history AS jsonb), :level, :freq_per_week, :session_time_min,
            :case_notes, CAST(:equipment AS jsonb), CAST(:red_flags AS jsonb), CAST(:readiness AS jsonb), CAST(:periodization AS jsonb), :status
        )
        RETURNING id, student_id, measurement_id, objectives, posture, injuries,
                  restrictions, history, level, freq_per_week, session_time_min,
                  case_notes, equipment, red_flags, readiness, periodization, status,
                  created_at;
    """), prepared).mappings().one()


def select_assessment_by_id(db: Session, assessment_id: int):
    return db.execute(text("""
        SELECT id, student_id, measurement_id, objectives, posture, injuries,
               restrictions, history, level, freq_per_week, session_time_min,
               case_notes, equipment, red_flags, readiness, periodization, status,
               created_at
        FROM assessments WHERE id = :aid;
    """), {"aid": assessment_id}).mappings().one_or_none()


def select_assessments_by_student(db: Session, student_id: int):
    return db.execute(text("""
        SELECT id, student_id, measurement_id, objectives, posture, injuries,
               restrictions, history, level, freq_per_week, session_time_min,
               case_notes, equipment, red_flags, readiness, periodization, status,
               created_at
        FROM assessments WHERE student_id = :sid ORDER BY id DESC;
    """), {"sid": student_id}).mappings().all()


def assessment_exists(db: Session, assessment_id: int) -> bool:
    return bool(db.execute(text("SELECT 1 FROM assessments WHERE id = :id;"), {"id": assessment_id}).scalar())


def update_assessment_fields(db: Session, data: dict[str, Any]):
    prepared = _prepare_assessment_data(data)
    return db.execute(text("""
        UPDATE assessments
        SET measurement_id   = COALESCE(:measurement_id,   measurement_id),
            objectives       = COALESCE(CAST(:objectives AS jsonb),       objectives),
            posture          = COALESCE(CAST(:posture AS jsonb),          posture),
            injuries         = COALESCE(CAST(:injuries AS jsonb),         injuries),
            restrictions     = COALESCE(CAST(:restrictions AS jsonb),     restrictions),
            history          = COALESCE(CAST(:history AS jsonb),          history),
            level            = COALESCE(:level,            level),
            freq_per_week    = COALESCE(:freq_per_week,    freq_per_week),
            session_time_min = COALESCE(:session_time_min, session_time_min),
            case_notes       = COALESCE(:case_notes,       case_notes),
            equipment        = COALESCE(CAST(:equipment AS jsonb),        equipment),
            red_flags        = COALESCE(CAST(:red_flags AS jsonb),        red_flags),
            readiness        = COALESCE(CAST(:readiness AS jsonb),        readiness),
            periodization    = COALESCE(CAST(:periodization AS jsonb),    periodization),
            status           = COALESCE(:status,           status)
        WHERE id = :id
        RETURNING id, student_id, measurement_id, objectives, posture, injuries,
                  restrictions, history, level, freq_per_week, session_time_min,
                  case_notes, equipment, red_flags, readiness, periodization, status,
                  created_at;
    """), prepared).mappings().one()


def delete_assessment_by_id(db: Session, assessment_id: int) -> int:
    return db.execute(text("DELETE FROM assessments WHERE id = :id;"), {"id": assessment_id}).rowcount
