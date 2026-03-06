# src/api/routes/students.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from src.db.database import get_db
from src.api.schemas.students import StudentCreate, StudentOut, StudentUpdate
from src.services.student_service import (
    create_student,
    get_student_by_id,
    get_student_by_cpf,
    list_students,
    update_student,
    delete_student,
)
from src.services.student_service import _normalize_cpf

router = APIRouter(prefix="/students", tags=["students"])


@router.post("/", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student_route(payload: StudentCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    return create_student(db, data)


@router.get("/", response_model=List[StudentOut])
def list_students_route(db: Session = Depends(get_db)):
    return list_students(db)


@router.get("/{student_id}", response_model=StudentOut)
def get_student_route(student_id: int, db: Session = Depends(get_db)):
    row = get_student_by_id(db, student_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return row


@router.get("/lookup", response_model=StudentOut)
def lookup_student(
    id: Optional[int] = Query(None),
    cpf: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    if id is None and cpf is None:
        raise HTTPException(status_code=400, detail="Informe id ou cpf.")
    if id is not None:
        row = get_student_by_id(db, id)
    else:
        row = get_student_by_cpf(db, cpf or "")
    if row is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return row


@router.put("/update", response_model=StudentOut)
def update_student_route(
    payload: StudentUpdate,
    id: int | None = Query(default=None),
    cpf: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    if id is None and cpf is None:
        raise HTTPException(status_code=400, detail="Informe id ou cpf.")
    if id is not None:
        current = get_student_by_id(db, id)
    else:
        current = get_student_by_cpf(db, cpf or "")
    if current is None:
        raise HTTPException(status_code=404, detail="Student not found")
    data = payload.model_dump(exclude_unset=True)
    return update_student(db, current["id"], data)


@router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
def delete_student_route(
    id: int | None = Query(default=None),
    cpf: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    if id is None and cpf is None:
        raise HTTPException(status_code=400, detail="Informe id ou cpf.")
    if id is not None:
        current = get_student_by_id(db, id)
    else:
        current = get_student_by_cpf(db, cpf or "")
    if current is None:
        raise HTTPException(status_code=404, detail="Student not found")
    ok = delete_student(db, current["id"])
    if not ok:
        raise HTTPException(status_code=404, detail="Student not found")
    return
