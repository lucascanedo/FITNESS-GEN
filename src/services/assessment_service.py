# src/services/assessment_service.py
from __future__ import annotations
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException

from src.repositories import assessment_repository


def create_assessment(db: Session, data: dict[str, Any]) -> dict[str, Any]:
    try:
        row = assessment_repository.insert_assessment(db, data)
        db.commit()
        return dict(row)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Erro ao criar assessment (verifique FKs e JSONs).")


def get_assessment(db: Session, assessment_id: int) -> dict[str, Any] | None:
    row = assessment_repository.select_assessment_by_id(db, assessment_id)
    return dict(row) if row else None


def list_assessments_by_student(db: Session, student_id: int) -> list[dict[str, Any]]:
    rows = assessment_repository.select_assessments_by_student(db, student_id)
    return [dict(r) for r in rows]


def update_assessment(db: Session, assessment_id: int, data: dict[str, Any]) -> dict[str, Any]:
    if not assessment_repository.assessment_exists(db, assessment_id):
        raise HTTPException(status_code=404, detail="Assessment not found")
    data["id"] = assessment_id
    try:
        row = assessment_repository.update_assessment_fields(db, data)
        db.commit()
        return dict(row)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Erro de integridade ao atualizar assessment.")


def delete_assessment(db: Session, assessment_id: int) -> bool:
    rowcount = assessment_repository.delete_assessment_by_id(db, assessment_id)
    db.commit()
    return rowcount > 0
