# src/api/routes/measurements.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.api.schemas.measurements import MeasurementCreate, MeasurementUpdate, MeasurementOut
from src.services.measurement_service import (
    create_measurement,
    get_measurement,
    list_measurements_by_student,
    update_measurement,
)

router = APIRouter(prefix="/measurements", tags=["measurements"])


@router.post("/", response_model=MeasurementOut, status_code=status.HTTP_201_CREATED)
def create_measurement_route(payload: MeasurementCreate, db: Session = Depends(get_db)):
    return create_measurement(db, payload.model_dump(exclude_unset=True))


@router.get("/student/{student_id}", response_model=list[MeasurementOut])
def list_measurements_route(student_id: int, db: Session = Depends(get_db)):
    return list_measurements_by_student(db, student_id)


@router.get("/{measurement_id}", response_model=MeasurementOut)
def get_measurement_route(measurement_id: int, db: Session = Depends(get_db)):
    row = get_measurement(db, measurement_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Measurement not found")
    return row


@router.put("/{measurement_id}", response_model=MeasurementOut)
def update_measurement_route(measurement_id: int, payload: MeasurementUpdate, db: Session = Depends(get_db)):
    return update_measurement(db, measurement_id, payload.model_dump(exclude_unset=True))


@router.delete("/{measurement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_measurement_route(measurement_id: int, db: Session = Depends(get_db)):
    from src.services.measurement_service import delete_measurement
    ok = delete_measurement(db, measurement_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Measurement not found")
    return
