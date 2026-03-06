# src/services/measurement_service.py
from __future__ import annotations
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException


def create_measurement(db: Session, data: dict[str, Any]) -> dict[str, Any]:
    stmt = text("""
        INSERT INTO measurements (
            student_id, measured_at, height_m, weight_kg, body_fat_percent,
            muscle_mass_kg, source, notes
        )
        VALUES (
            :student_id, :measured_at, :height_m, :weight_kg, :body_fat_percent,
            :muscle_mass_kg, :source, :notes
        )
        RETURNING id, student_id, measured_at, height_m, weight_kg,
                  body_fat_percent, muscle_mass_kg,
                  ROUND(bmi::numeric, 2) AS bmi,
                  source, notes, created_at;
    """)
    try:
        row = db.execute(stmt, data).mappings().one()
        db.commit()
        return dict(row)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Erro ao inserir medição (verifique student_id e measured_at)."
        )


def get_measurement(db: Session, measurement_id: int) -> dict[str, Any] | None:
    row = db.execute(text("""
        SELECT id, student_id, measured_at, height_m, weight_kg,
               body_fat_percent, muscle_mass_kg,
               ROUND(bmi::numeric, 2) AS bmi,
               source, notes, created_at
        FROM measurements WHERE id = :mid;
    """), {"mid": measurement_id}).mappings().one_or_none()
    return dict(row) if row else None


def list_measurements_by_student(db: Session, student_id: int) -> list[dict[str, Any]]:
    rows = db.execute(text("""
        SELECT id, student_id, measured_at, height_m, weight_kg,
               body_fat_percent, muscle_mass_kg,
               ROUND(bmi::numeric, 2) AS bmi,
               source, notes, created_at
        FROM measurements WHERE student_id = :sid ORDER BY measured_at DESC;
    """), {"sid": student_id}).mappings().all()
    return [dict(r) for r in rows]


def update_measurement(db: Session, measurement_id: int, data: dict[str, Any]) -> dict[str, Any]:
    exists = db.execute(text("SELECT 1 FROM measurements WHERE id = :id;"), {"id": measurement_id}).scalar()
    if not exists:
        raise HTTPException(status_code=404, detail="Measurement not found")
    data["id"] = measurement_id
    stmt = text("""
        UPDATE measurements
        SET measured_at       = COALESCE(:measured_at, measured_at),
            height_m          = COALESCE(:height_m, height_m),
            weight_kg         = COALESCE(:weight_kg, weight_kg),
            body_fat_percent  = COALESCE(:body_fat_percent, body_fat_percent),
            muscle_mass_kg    = COALESCE(:muscle_mass_kg, muscle_mass_kg),
            source            = COALESCE(:source, source),
            notes             = COALESCE(:notes, notes)
        WHERE id = :id
        RETURNING id, student_id, measured_at, height_m, weight_kg,
                  body_fat_percent, muscle_mass_kg,
                  ROUND(bmi::numeric, 2) AS bmi,
                  source, notes, created_at;
    """)
    try:
        row = db.execute(stmt, data).mappings().one()
        db.commit()
        return dict(row)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Erro de integridade ao atualizar medição.")


def delete_measurement(db: Session, measurement_id: int) -> bool:
    res = db.execute(text("DELETE FROM measurements WHERE id = :id;"), {"id": measurement_id})
    db.commit()
    return res.rowcount > 0
