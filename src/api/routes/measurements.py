# src/api/routes/measurements.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from typing import List

from src.db.database import get_db
from src.api.schemas.measurements import (
    MeasurementCreate, MeasurementUpdate, MeasurementOut
)

router = APIRouter(prefix="/measurements", tags=["measurements"])

# --------------------------
# CREATE
# --------------------------
@router.post("/", response_model=MeasurementOut, status_code=status.HTTP_201_CREATED)
def create_measurement(payload: MeasurementCreate, db: Session = Depends(get_db)):
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
        row = db.execute(stmt, payload.model_dump(exclude_unset=True)).mappings().one()
        db.commit()
        return dict(row)
    except IntegrityError:
        db.rollback()
        # FK student_id inválido ou violação do índice único (student_id, measured_at)
        raise HTTPException(
            status_code=400,
            detail="Erro ao inserir medição (verifique student_id e se measured_at não colide com outra medição do mesmo aluno)."
        )

# --------------------------
# READ - lista por aluno
# --------------------------
@router.get("/student/{student_id}", response_model=List[MeasurementOut])
def list_measurements_by_student(student_id: int, db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT id, student_id, measured_at, height_m, weight_kg,
               body_fat_percent, muscle_mass_kg,
               ROUND(bmi::numeric, 2) AS bmi,
               source, notes, created_at
        FROM measurements
        WHERE student_id = :sid
        ORDER BY measured_at DESC;
    """), {"sid": student_id}).mappings().all()
    return [dict(r) for r in rows]

# --------------------------
# READ - por id
# --------------------------
@router.get("/{measurement_id}", response_model=MeasurementOut)
def get_measurement(measurement_id: int, db: Session = Depends(get_db)):
    row = db.execute(text("""
        SELECT id, student_id, measured_at, height_m, weight_kg,
               body_fat_percent, muscle_mass_kg,
               ROUND(bmi::numeric, 2) AS bmi,
               source, notes, created_at
        FROM measurements
        WHERE id = :mid;
    """), {"mid": measurement_id}).mappings().one_or_none()

    if row is None:
        raise HTTPException(status_code=404, detail="Measurement not found")
    return dict(row)

# --------------------------
# UPDATE - por id (parcial)
# --------------------------
@router.put("/{measurement_id}", response_model=MeasurementOut)
def update_measurement(measurement_id: int, payload: MeasurementUpdate, db: Session = Depends(get_db)):
    # garante que existe
    current = db.execute(text("SELECT id FROM measurements WHERE id = :id;"),
                         {"id": measurement_id}).mappings().one_or_none()
    if current is None:
        raise HTTPException(status_code=404, detail="Measurement not found")

    data = payload.model_dump(exclude_unset=True)

    # Trigger BEFORE UPDATE já recalcula BMI quando height/weight mudam.
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
        row = db.execute(stmt, {**data, "id": measurement_id}).mappings().one()
        db.commit()
        return dict(row)
    except IntegrityError:
        db.rollback()
        # Pode ser colisão no índice único (student_id, measured_at)
        raise HTTPException(
            status_code=400,
            detail="Erro de integridade ao atualizar medição (confira measured_at para não duplicar no mesmo aluno)."
        )

# --------------------------
# DELETE - por id
# --------------------------
@router.delete("/{measurement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_measurement(measurement_id: int, db: Session = Depends(get_db)):
    res = db.execute(text("DELETE FROM measurements WHERE id = :id;"), {"id": measurement_id})
    db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Measurement not found")
    return
