from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def insert_assessment(db: Session, data: dict[str, Any]):
    return db.execute(text("""
        INSERT INTO assessments (
            student_id, measurement_id, objectives, posture, injuries, restrictions,
            history, level, freq_per_week, session_time_min,
            case_notes, equipment, red_flags, readiness, periodization, status
        )
        VALUES (
            :student_id, :measurement_id, :objectives, :posture, :injuries, :restrictions,
            :history, :level, :freq_per_week, :session_time_min,
            :case_notes, :equipment, :red_flags, :readiness, :periodization, :status
        )
        RETURNING id, student_id, measurement_id, objectives, posture, injuries,
                  restrictions, history, level, freq_per_week, session_time_min,
                  case_notes, equipment, red_flags, readiness, periodization, status,
                  created_at;
    """), data).mappings().one()


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
    return db.execute(text("""
        UPDATE assessments
        SET measurement_id   = COALESCE(:measurement_id,   measurement_id),
            objectives       = COALESCE(:objectives,       objectives),
            posture          = COALESCE(:posture,          posture),
            injuries         = COALESCE(:injuries,         injuries),
            restrictions     = COALESCE(:restrictions,     restrictions),
            history          = COALESCE(:history,          history),
            level            = COALESCE(:level,            level),
            freq_per_week    = COALESCE(:freq_per_week,    freq_per_week),
            session_time_min = COALESCE(:session_time_min, session_time_min),
            case_notes       = COALESCE(:case_notes,       case_notes),
            equipment        = COALESCE(:equipment,        equipment),
            red_flags        = COALESCE(:red_flags,        red_flags),
            readiness        = COALESCE(:readiness,        readiness),
            periodization    = COALESCE(:periodization,    periodization),
            status           = COALESCE(:status,           status)
        WHERE id = :id
        RETURNING id, student_id, measurement_id, objectives, posture, injuries,
                  restrictions, history, level, freq_per_week, session_time_min,
                  case_notes, equipment, red_flags, readiness, periodization, status,
                  created_at;
    """), data).mappings().one()


def delete_assessment_by_id(db: Session, assessment_id: int) -> int:
    return db.execute(text("DELETE FROM assessments WHERE id = :id;"), {"id": assessment_id}).rowcount
