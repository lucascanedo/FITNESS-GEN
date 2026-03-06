# src/api/routes/llm.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.api.schemas.plans import PlanBody, PlanGenerationResponse
from src.services.llm_service import (
    generate_plan_with_learning_context,
    log_llm_call,
)

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
