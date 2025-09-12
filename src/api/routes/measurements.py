from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from src.db.database import get_db
from src.api.schemas.measurements import MeasurementCreate, MeasurementOut
from typing import List

router = APIRouter(prefix="/measurements", tags=["measurements"])

@router.post("", response_model=MeasurementOut, status_code=status.HTTP_201_CREATED)
def create_measurement(payload: MeasurementCreate, db: Session = Depends(get_db)):
    # INSERT usando RETURNING para trazer bmi e created_at calculados no banco
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
                  body_fat_percent, muscle_mass_kg, bmi, source, notes, created_at;
    """)
    try:
        row = db.execute(stmt, payload.model_dump()).mappings().one()
        db.commit()
        return row
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Erro ao inserir medição (verifique student_id válido).")

@router.get("/student/{student_id}", response_model=List[MeasurementOut])
def list_measurements_by_student(student_id: int, db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT id, student_id, measured_at, height_m, weight_kg,
               body_fat_percent, muscle_mass_kg, bmi, source, notes, created_at
        FROM measurements
        WHERE student_id = :sid
        ORDER BY measured_at DESC;
    """), {"sid": student_id}).mappings().all()
    return rows

@router.get("/{measurement_id}", response_model=MeasurementOut)
def get_measurement(measurement_id: int, db: Session = Depends(get_db)):
    row = db.execute(text("""
        SELECT id, student_id, measured_at, height_m, weight_kg,
               body_fat_percent, muscle_mass_kg, bmi, source, notes, created_at
        FROM measurements
        WHERE id = :mid;
    """), {"mid": measurement_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Measurement not found")
    return row
