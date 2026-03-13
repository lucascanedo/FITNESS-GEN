# src/api/routes/llm.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.api.schemas.plans import PlanBody, PlanGenerationResponse
from src.services.assessment_service import get_assessment
from src.services.llm_service import (
    generate_plan_with_learning_context,
    log_llm_call,
)
from src.services.measurement_service import get_measurement
from src.services.student_service import get_student_by_id

router = APIRouter(prefix="/llm", tags=["llm"])


@router.post(
    "/generate-plan/student/{student_id}/assessment/{assessment_id}/measurement/{measurement_id}",
    response_model=PlanGenerationResponse,
)
def generate_plan_for_edit(
    student_id: int,
    assessment_id: int,
    measurement_id: int,
    db: Session = Depends(get_db),
    request: Request = None,
):
    """
    Gera rascunho de plano via LLM com contexto de aprendizado.
    NÃO persiste no banco; o treinador edita e salva via POST /plans.
    """
    correlation_id = getattr(request.state, "correlation_id", None)

    student = get_student_by_id(db, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    assessment = get_assessment(db, assessment_id)
    if assessment is None or assessment.get("student_id") != student_id:
        raise HTTPException(status_code=400, detail="Assessment invalido para este aluno.")

    measurement = get_measurement(db, measurement_id)
    if measurement is None or measurement.get("student_id") != student_id:
        raise HTTPException(status_code=400, detail="Measurement invalida para este aluno.")

    try:
        plan_dict, meta = generate_plan_with_learning_context(
            db, student_id, assessment_id, measurement_id, correlation_id=correlation_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erro na geração do plano: {e}")

    meta["resp_raw"] = meta.get("resp_raw", "")[:5000]

    try:
        plan_body = PlanBody.model_validate(plan_dict)
    except Exception as e:
        meta["error"] = str(e)
        log_llm_call(db, meta)
        raise HTTPException(status_code=502, detail=f"Plano inválido do LLM: {e}")

    llm_call_id = log_llm_call(db, meta)
    return PlanGenerationResponse(plan=plan_body, llm_call_id=llm_call_id)
