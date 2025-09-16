from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.IA.llm_helpers import get_llm_bundle         # valida 3 IDs e monta bundle
from src.IA.llm_generator import LLMGenerator       # monta prompt, chama Groq e retorna JSON
from src.api.schemas.plans import PlanBody           # valida o JSON antes de devolver

router = APIRouter(prefix="/llm", tags=["llm"])

@router.post(
    "/generate-plan/student/{student_id}/assessment/{assessment_id}/measurement/{measurement_id}",
    response_model=PlanBody
)
def generate_plan_for_edit(
    student_id: int,
    assessment_id: int,
    measurement_id: int,
    enforce_snapshot_match: bool = False,
    db: Session = Depends(get_db),
):
    """
    1) Valida os 3 IDs e carrega dados (helper)
    2) Gera plano via LLM (generator)
    3) Retorna JSON editável (PlanBody) para o front — NÃO salva no banco
    """
    bundle = get_llm_bundle(
        db=db,
        student_id=student_id,
        assessment_id=assessment_id,
        measurement_id=measurement_id,
        enforce_snapshot_match=enforce_snapshot_match,
    )

    llm = LLMGenerator()
    plan_dict = llm.generate_plan(bundle)

    try:
        return PlanBody.model_validate(plan_dict)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Plano inválido do LLM: {e}")
