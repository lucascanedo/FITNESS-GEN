# src/api/routes/assessments.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.api.schemas.assessments import AssessmentCreate, AssessmentUpdate, AssessmentOut
from src.services.assessment_service import (
    create_assessment,
    get_assessment,
    list_assessments_by_student,
    update_assessment,
    delete_assessment,
)

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.post("/", response_model=AssessmentOut, status_code=status.HTTP_201_CREATED)
def create_assessment_route(payload: AssessmentCreate, db: Session = Depends(get_db)):
    return create_assessment(db, payload.model_dump(exclude_unset=True))


@router.get("/student/{student_id}", response_model=list[AssessmentOut])
def list_assessments_route(student_id: int, db: Session = Depends(get_db)):
    return list_assessments_by_student(db, student_id)


@router.get("/{assessment_id}", response_model=AssessmentOut)
def get_assessment_route(assessment_id: int, db: Session = Depends(get_db)):
    row = get_assessment(db, assessment_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return row


@router.put("/{assessment_id}", response_model=AssessmentOut)
def update_assessment_route(assessment_id: int, payload: AssessmentUpdate, db: Session = Depends(get_db)):
    return update_assessment(db, assessment_id, payload.model_dump(exclude_unset=True))


@router.delete("/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assessment_route(assessment_id: int, db: Session = Depends(get_db)):
    ok = delete_assessment(db, assessment_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return
