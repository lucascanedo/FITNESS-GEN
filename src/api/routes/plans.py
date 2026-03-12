# src/api/routes/plans.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.db.database import get_db
from src.api.schemas.plans import PlanCreate, PlanOut, PlanUpdate
from src.services.plan_service import (
    create_plan,
    create_plan_from_llm,
    update_plan,
    get_plan,
    get_current_student_plan,
    get_student_plans,
    delete_plan,
)
from src.services.plan_analysis_service import (
    analyze_plan_differences,
    build_student_plan_mcp_context,
    get_professor_edit_patterns,
    get_plan_comparison,
    get_professor_learning_diagnostics,
)

router = APIRouter(prefix="/plans", tags=["plans"])


def _resolve_llm_call_id(db: Session, correlation_id: str | None, llm_call_id: int | None) -> int | None:
    if llm_call_id is not None:
        return llm_call_id
    if correlation_id:
        row = db.execute(
            text("SELECT id FROM llm_calls WHERE correlation_id = :cid ORDER BY id DESC LIMIT 1;"),
            {"cid": correlation_id}
        ).mappings().one_or_none()
        return row["id"] if row else None
    return None


@router.post("/", response_model=PlanOut, status_code=201)
def create_plan_route(payload: PlanCreate, db: Session = Depends(get_db), request: Request = None):
    """
    Cria plano a partir do JSON editado pelo treinador.
    Aceita generated_plan_json/llm_call_id/correlation_id para vincular ao LLM.
    """
    llm_id = _resolve_llm_call_id(
        db,
        payload.correlation_id or getattr(request.state, "correlation_id", None),
        payload.llm_call_id,
    )
    plan = create_plan(
        db=db,
        student_id=payload.student_id,
        assessment_id=payload.assessment_id,
        measurement_id=payload.measurement_id,
        plan_meta=payload.plan_meta.model_dump(),
        items=[it.model_dump() for it in payload.items],
        generated_plan_json=payload.generated_plan_json,
        llm_call_id=llm_id,
    )
    if llm_id:
        db.execute(text("UPDATE llm_calls SET plan_id = :pid WHERE id = :lid;"), {"pid": plan["id"], "lid": llm_id})
        db.commit()
    return plan


@router.get("/edit-patterns")
def get_edit_patterns_route(student_id: int | None = None, db: Session = Depends(get_db)):
    return get_professor_edit_patterns(db, student_id)


@router.get("/learning-diagnostics")
def get_learning_diagnostics_route(student_id: int | None = None, db: Session = Depends(get_db)):
    return get_professor_learning_diagnostics(db, student_id)


@router.get("/student/{student_id}/current", response_model=PlanOut)
def get_current_plan_route(student_id: int, db: Session = Depends(get_db)):
    plan = get_current_student_plan(db, student_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Current plan not found")
    return plan


@router.get("/student/{student_id}/mcp-context")
def get_student_plan_mcp_context_route(student_id: int, db: Session = Depends(get_db)):
    return build_student_plan_mcp_context(db, student_id)


@router.get("/{plan_id}", response_model=PlanOut)
def get_plan_route(plan_id: int, db: Session = Depends(get_db)):
    plan = get_plan(db, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.get("/student/{student_id}", response_model=list[PlanOut])
def list_plans_route(student_id: int, db: Session = Depends(get_db)):
    return get_student_plans(db, student_id)


@router.put("/{plan_id}", response_model=PlanOut)
def update_plan_route(plan_id: int, payload: PlanUpdate, db: Session = Depends(get_db)):
    return update_plan(
        db,
        plan_id,
        payload.plan_meta.model_dump() if payload.plan_meta else None,
        [it.model_dump() for it in payload.items] if payload.items else None,
    )


@router.delete("/{plan_id}", status_code=204)
def delete_plan_route(plan_id: int, db: Session = Depends(get_db)):
    ok = delete_plan(db, plan_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Plan not found")
    return


@router.get("/{plan_id}/analysis")
def get_plan_analysis(plan_id: int, db: Session = Depends(get_db)):
    result = analyze_plan_differences(db, plan_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/{plan_id}/comparison")
def get_plan_comparison_route(plan_id: int, db: Session = Depends(get_db)):
    comparison = get_plan_comparison(db, plan_id)
    if comparison is None:
        raise HTTPException(status_code=404, detail="Comparison not found")
    return comparison
