# src/api/routes/plans.py
from __future__ import annotations
import json
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, requests
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from src.db.database import get_db
from src.api.schemas.plans import (
    PlanBody, PlanCreate, PlanOut, PlanItem, PlanMeta, PlanUpdate
)

router = APIRouter(prefix="/plans", tags=["plans"])

# -----------------------------------------------------------------------------
# CREATE
# -----------------------------------------------------------------------------
@router.post("/", response_model=PlanOut, status_code=status.HTTP_201_CREATED)
def create_plan(payload: PlanCreate, db: Session = Depends(get_db), request: requests = None):
    """
    Recebe o JSON final editado (plan_meta + items) e salva no banco
    amarrando student_id, assessment_id e measurement_id.
    Depois vincula ao llm_calls (se houver correlation_id).
    """
    # valida FKs e pertença ao mesmo aluno
    chk = db.execute(text("""
        SELECT
          (SELECT student_id FROM assessments  WHERE id = :aid) AS a_sid,
          (SELECT student_id FROM measurements WHERE id = :mid) AS m_sid,
          (SELECT 1          FROM students     WHERE id = :sid) AS s_ok
    """), {
        "sid": payload.student_id,
        "aid": payload.assessment_id,
        "mid": payload.measurement_id
    }).mappings().one()

    if chk["s_ok"] is None:
        raise HTTPException(status_code=400, detail="student_id inválido.")
    if chk["a_sid"] is None or chk["m_sid"] is None:
        raise HTTPException(status_code=400, detail="assessment_id ou measurement_id inválidos.")
    if not (chk["a_sid"] == payload.student_id and chk["m_sid"] == payload.student_id):
        raise HTTPException(status_code=400, detail="IDs não pertencem ao mesmo aluno.")

    plan_blob = {
        "plan_meta": payload.plan_meta.model_dump(),
        "items": [it.model_dump() for it in payload.items],
    }

    try:
        row = db.execute(text("""
            INSERT INTO plans (student_id, assessment_id, measurement_id, plan_json)
            VALUES (:sid, :aid, :mid, :pjson)
            RETURNING id, student_id, assessment_id, measurement_id, plan_json, created_at;
        """), {
            "sid": payload.student_id,
            "aid": payload.assessment_id,
            "mid": payload.measurement_id,
            "pjson": json.dumps(plan_blob, ensure_ascii=False)
        }).mappings().one()

        plan_id = row["id"]

        # 🔗 tenta vincular no llm_calls
        cid = getattr(request.state, "correlation_id", None)
        if cid:
            db.execute(text("""
                UPDATE llm_calls
                SET plan_id = :pid
                WHERE correlation_id = :cid
            """), {"pid": plan_id, "cid": cid})

        db.commit()
        return dict(row)

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Erro ao salvar plano.")

# -----------------------------------------------------------------------------
# READs
# -----------------------------------------------------------------------------
@router.get("/{plan_id}", response_model=PlanOut)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    row = db.execute(text("""
        SELECT id, student_id, assessment_id, measurement_id, plan_json, created_at
        FROM plans
        WHERE id = :pid;
    """), {"pid": plan_id}).mappings().one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return dict(row)

@router.get("/student/{student_id}", response_model=List[PlanOut])
def list_plans_by_student(student_id: int, db: Session = Depends(get_db)):
    rows = db.execute(text("""
        SELECT id, student_id, assessment_id, measurement_id, plan_json, created_at
        FROM plans
        WHERE student_id = :sid
        ORDER BY id DESC;
    """), {"sid": student_id}).mappings().all()
    return [dict(r) for r in rows]


# -----------------------------------------------------------------------------
# UPDATE
# -----------------------------------------------------------------------------
@router.put("/{plan_id}", response_model=PlanOut)
def update_plan(plan_id: int, payload: PlanUpdate, db: Session = Depends(get_db)):
    row = db.execute(text("SELECT plan_json FROM plans WHERE id = :id;"),
                     {"id": plan_id}).mappings().one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Plan not found")

    current = row["plan_json"]
    if isinstance(current, str):
        current = json.loads(current)

    if payload.plan_meta is not None:
        meta = payload.plan_meta.model_dump()
        current["plan_meta"] = {**current.get("plan_meta", {}), **meta}

    if payload.items is not None:
        current["items"] = [it.model_dump() for it in payload.items]

    try:
        row2 = db.execute(text("""
            UPDATE plans
            SET plan_json = :pjson
            WHERE id = :id
            RETURNING id, student_id, assessment_id, measurement_id, plan_json, created_at;
        """), {"pjson": json.dumps(current, ensure_ascii=False), "id": plan_id}).mappings().one()
        db.commit()
        return dict(row2)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Erro ao atualizar plano.")


# -----------------------------------------------------------------------------
# DELETE
# -----------------------------------------------------------------------------
@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    res = db.execute(text("DELETE FROM plans WHERE id = :id;"), {"id": plan_id})
    db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Plan not found")
    return
