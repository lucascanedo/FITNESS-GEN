# src/services/measurement_service.py
from __future__ import annotations
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi import HTTPException

from src.repositories import measurement_repository


def create_measurement(db: Session, data: dict[str, Any]) -> dict[str, Any]:
    try:
        row = measurement_repository.insert_measurement(db, data)
        db.commit()
        return dict(row)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Erro ao inserir medição (verifique student_id e measured_at)."
        )


def get_measurement(db: Session, measurement_id: int) -> dict[str, Any] | None:
    row = measurement_repository.select_measurement_by_id(db, measurement_id)
    return dict(row) if row else None


def list_measurements_by_student(db: Session, student_id: int) -> list[dict[str, Any]]:
    rows = measurement_repository.select_measurements_by_student(db, student_id)
    return [dict(r) for r in rows]


def update_measurement(db: Session, measurement_id: int, data: dict[str, Any]) -> dict[str, Any]:
    if not measurement_repository.measurement_exists(db, measurement_id):
        raise HTTPException(status_code=404, detail="Measurement not found")
    data["id"] = measurement_id
    try:
        row = measurement_repository.update_measurement_fields(db, data)
        db.commit()
        return dict(row)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Erro de integridade ao atualizar medição.")


def delete_measurement(db: Session, measurement_id: int) -> bool:
    rowcount = measurement_repository.delete_measurement_by_id(db, measurement_id)
    db.commit()
    return rowcount > 0
