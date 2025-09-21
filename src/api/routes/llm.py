# src/api/routes/llm.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.db.database import get_db
from src.IA.llm_helpers import get_llm_bundle
from src.IA.llm_generator import LLMGenerator
from src.api.schemas.plans import PlanBody

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

    # Adiciona raw da resposta ao meta
    meta["resp_raw"] = meta.get("resp_raw", "")[:5000]  # opcional truncar a 5000 chars

    # 3) valida estrutura (não salva plano; só responde ao front)
    try:
        plan_body = PlanBody.model_validate(plan_dict)
    except Exception as e:
        # loga erro
        try:
            db.execute(text("""
                INSERT INTO llm_calls (
                  correlation_id, route, provider, model, prompt_hash, prompt_len,
                  resp_len, duration_ms, error, resp_raw,
                  student_id, assessment_id, measurement_id
                )
                VALUES (:cid, :route, :prov, :model, :ph, :pl, :rl, :dur, :err, :raw, :sid, :aid, :mid)
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
                "raw": meta.get("resp_raw"),
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
              correlation_id, route, provider, model, prompt_hash, prompt_len,
              resp_len, duration_ms, error, resp_raw,
              student_id, assessment_id, measurement_id
            )
            VALUES (:cid, :route, :prov, :model, :ph, :pl, :rl, :dur, :err, :raw, :sid, :aid, :mid)
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
            "raw": meta.get("resp_raw"),
            "sid": student_id,
            "aid": assessment_id,
            "mid": measurement_id
        })
        db.commit()
    except Exception:
        db.rollback()

    return plan_body
