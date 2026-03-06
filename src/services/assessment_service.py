# src/services/assessment_service.py
from __future__ import annotations
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException


def create_assessment(db: Session, data: dict[str, Any]) -> dict[str, Any]:
    stmt = text("""
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
    """)
    try:
        row = db.execute(stmt, data).mappings().one()
        db.commit()
        return dict(row)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Erro ao criar assessment (verifique FKs e JSONs).")


def get_assessment(db: Session, assessment_id: int) -> dict[str, Any] | None:
    row = db.execute(text("""
        SELECT id, student_id, measurement_id, objectives, posture, injuries,
               restrictions, history, level, freq_per_week, session_time_min,
               case_notes, equipment, red_flags, readiness, periodization, status,
               created_at
        FROM assessments WHERE id = :aid;
    """), {"aid": assessment_id}).mappings().one_or_none()
    return dict(row) if row else None


def list_assessments_by_student(db: Session, student_id: int) -> list[dict[str, Any]]:
    rows = db.execute(text("""
        SELECT id, student_id, measurement_id, objectives, posture, injuries,
               restrictions, history, level, freq_per_week, session_time_min,
               case_notes, equipment, red_flags, readiness, periodization, status,
               created_at
        FROM assessments WHERE student_id = :sid ORDER BY id DESC;
    """), {"sid": student_id}).mappings().all()
    return [dict(r) for r in rows]


def update_assessment(db: Session, assessment_id: int, data: dict[str, Any]) -> dict[str, Any]:
    exists = db.execute(text("SELECT 1 FROM assessments WHERE id = :id;"), {"id": assessment_id}).scalar()
    if not exists:
        raise HTTPException(status_code=404, detail="Assessment not found")
    data["id"] = assessment_id
    stmt = text("""
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
    """)
    try:
        row = db.execute(stmt, data).mappings().one()
        db.commit()
        return dict(row)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Erro de integridade ao atualizar assessment.")


def delete_assessment(db: Session, assessment_id: int) -> bool:
    res = db.execute(text("DELETE FROM assessments WHERE id = :id;"), {"id": assessment_id})
    db.commit()
    return res.rowcount > 0
