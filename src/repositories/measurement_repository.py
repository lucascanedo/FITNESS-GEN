from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def insert_measurement(db: Session, data: dict[str, Any]):
    return db.execute(text("""
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
    """), data).mappings().one()


def select_measurement_by_id(db: Session, measurement_id: int):
    return db.execute(text("""
        SELECT id, student_id, measured_at, height_m, weight_kg,
               body_fat_percent, muscle_mass_kg,
               ROUND(bmi::numeric, 2) AS bmi,
               source, notes, created_at
        FROM measurements WHERE id = :mid;
    """), {"mid": measurement_id}).mappings().one_or_none()


def select_measurements_by_student(db: Session, student_id: int):
    return db.execute(text("""
        SELECT id, student_id, measured_at, height_m, weight_kg,
               body_fat_percent, muscle_mass_kg,
               ROUND(bmi::numeric, 2) AS bmi,
               source, notes, created_at
        FROM measurements WHERE student_id = :sid ORDER BY measured_at DESC;
    """), {"sid": student_id}).mappings().all()


def measurement_exists(db: Session, measurement_id: int) -> bool:
    return bool(db.execute(text("SELECT 1 FROM measurements WHERE id = :id;"), {"id": measurement_id}).scalar())


def update_measurement_fields(db: Session, data: dict[str, Any]):
    return db.execute(text("""
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
    """), data).mappings().one()


def delete_measurement_by_id(db: Session, measurement_id: int) -> int:
    return db.execute(text("DELETE FROM measurements WHERE id = :id;"), {"id": measurement_id}).rowcount
