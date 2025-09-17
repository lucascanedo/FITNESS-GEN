# src/api/routes/assessments.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from typing import List

from src.db.database import get_db
from src.api.schemas.assessments import (
    AssessmentCreate, AssessmentUpdate, AssessmentOut
)

router = APIRouter(prefix="/assessments", tags=["assessments"])

# --------------------------
# CREATE
# --------------------------
@router.post("/", response_model=AssessmentOut, status_code=status.HTTP_201_CREATED)
def create_assessment(payload: AssessmentCreate, db: Session = Depends(get_db)):
    """
    Cria uma anamnese rica (dossiê) para um aluno.
    Serve de insumo direto para geração de plano via LLM.
    """
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
        row = db.execute(stmt, payload.model_dump(exclude_unset=True)).mappings().one()
        db.commit()
        return dict(row)
    except IntegrityError:
        db.rollback()
        # Possível FK inválida (student_id/measurement_id) ou tipos JSON malformados
        raise HTTPException(status_code=400, detail="Erro ao criar assessment (verifique FKs e JSONs).")

# --------------------------
# LIST by student
# --------------------------
@router.get("/student/{student_id}", response_model=List[AssessmentOut])
def list_assessments_by_student(student_id: int, db: Session = Depends(get_db)):
    """
    Lista anamneses do aluno (mais recente primeiro).
    """
    rows = db.execute(text("""
        SELECT id, student_id, measurement_id, objectives, posture, injuries,
               restrictions, history, level, freq_per_week, session_time_min,
               case_notes, equipment, red_flags, readiness, periodization, status,
               created_at
        FROM assessments
        WHERE student_id = :sid
        ORDER BY id DESC;
    """), {"sid": student_id}).mappings().all()
    return [dict(r) for r in rows]

# --------------------------
# GET by id
# --------------------------
@router.get("/{assessment_id}", response_model=AssessmentOut)
def get_assessment(assessment_id: int, db: Session = Depends(get_db)):
    row = db.execute(text("""
        SELECT id, student_id, measurement_id, objectives, posture, injuries,
               restrictions, history, level, freq_per_week, session_time_min,
               case_notes, equipment, red_flags, readiness, periodization, status,
               created_at
        FROM assessments
        WHERE id = :aid;
    """), {"aid": assessment_id}).mappings().one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return dict(row)

# --------------------------
# UPDATE (parcial) by id
# --------------------------
@router.put("/{assessment_id}", response_model=AssessmentOut)
def update_assessment(assessment_id: int, payload: AssessmentUpdate, db: Session = Depends(get_db)):
    """
    Atualização parcial: envie apenas os campos que deseja alterar.
    """
    # garante existência
    exists = db.execute(text("SELECT 1 FROM assessments WHERE id = :id;"),
                        {"id": assessment_id}).scalar()
    if not exists:
        raise HTTPException(status_code=404, detail="Assessment not found")

    data = payload.model_dump(exclude_unset=True)

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
        row = db.execute(stmt, {**data, "id": assessment_id}).mappings().one()
        db.commit()
        return dict(row)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Erro de integridade ao atualizar assessment.")

# --------------------------
# DELETE by id
# --------------------------
@router.delete("/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assessment(assessment_id: int, db: Session = Depends(get_db)):
    res = db.execute(text("DELETE FROM assessments WHERE id = :id;"), {"id": assessment_id})
    db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return
