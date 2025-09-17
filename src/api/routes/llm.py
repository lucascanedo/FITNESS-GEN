from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text

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
    request: Request = None,
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
    plan_dict, meta = llm.generate_plan(
            bundle,
            correlation_id=getattr(request.state, "correlation_id", None)
        )

    # 3) valida estrutura (não salva plano; só responde ao front)
    try:
        plan_body = PlanBody.model_validate(plan_dict)
    except Exception as e:
        # mesmo se der erro, vamos logar a chamada com 'error'
        try:
            db.execute(text("""
                INSERT INTO llm_calls (
                  correlation_id, route, provider, model, prompt_hash, prompt_len, resp_len, duration_ms, error,
                  student_id, assessment_id, measurement_id
                )
                VALUES (:cid, :route, :prov, :model, :ph, :pl, :rl, :dur, :err, :sid, :aid, :mid)
            """), {
                "cid": meta.get("correlation_id"),
                "route": "/llm/generate-plan",
                "prov": meta.get("provider"),
                "model": meta.get("model"),
                "ph": meta.get("prompt_hash"),
                "pl": meta.get("prompt_len"),
                "rl": meta.get("resp_len"),
                "dur": meta.get("duration_ms"),
                "err": meta.get("error") or str(e),
                "sid": student_id,
                "aid": assessment_id,
                "mid": measurement_id
            })
            db.commit()
        except Exception:
            db.rollback()
        raise HTTPException(status_code=502, detail=f"Plano inválido do LLM: {e}")

    # 4) grava auditoria OK
    try:
        db.execute(text("""
            INSERT INTO llm_calls (
              correlation_id, route, provider, model, prompt_hash, prompt_len, resp_len, duration_ms, error,
              student_id, assessment_id, measurement_id
            )
            VALUES (:cid, :route, :prov, :model, :ph, :pl, :rl, :dur, :err, :sid, :aid, :mid)
        """), {
            "cid": meta.get("correlation_id"),
            "route": "/llm/generate-plan",
            "prov": meta.get("provider"),
            "model": meta.get("model"),
            "ph": meta.get("prompt_hash"),
            "pl": meta.get("prompt_len"),
            "rl": meta.get("resp_len"),
            "dur": meta.get("duration_ms"),
            "err": meta.get("error"),
            "sid": student_id,
            "aid": assessment_id,
            "mid": measurement_id
        })
        db.commit()
    except Exception:
        db.rollback()  # não quebra a resposta

    return plan_body