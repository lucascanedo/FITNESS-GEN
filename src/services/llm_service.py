"""
Orquestracao do LLM: construcao de contexto, geracao e log.
O fluxo interno usa services diretamente; MCP permanece opcional para agentes externos.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from src.IA.llm_generator import LLMGenerator
from src.services.llm_context_service import build_generation_context
from src.services.plan_analysis_service import build_student_plan_mcp_context


def build_generation_payload(
    db: Session,
    student_id: int,
    assessment_id: int,
    measurement_id: int,
    include_learning: bool = True,
    include_current_plan: bool = True,
) -> dict[str, Any]:
    generation_context = build_generation_context(
        db=db,
        student_id=student_id,
        assessment_id=assessment_id,
        measurement_id=measurement_id,
        include_learning=include_learning,
    )
    payload: dict[str, Any] = {
        "student_id": student_id,
        "assessment_id": assessment_id,
        "measurement_id": measurement_id,
        "generation_context": generation_context,
    }
    if include_current_plan:
        payload["current_plan_context"] = build_student_plan_mcp_context(db, student_id)
    return payload


def generate_plan_with_learning_context(
    db: Session,
    student_id: int,
    assessment_id: int,
    measurement_id: int,
    correlation_id: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    context_payload = build_generation_payload(
        db=db,
        student_id=student_id,
        assessment_id=assessment_id,
        measurement_id=measurement_id,
        include_learning=True,
        include_current_plan=True,
    )
    llm = LLMGenerator()
    plan_dict, meta = llm.generate_plan(context_payload, correlation_id=correlation_id)

    generation_context = context_payload.get("generation_context") or {}
    learning = generation_context.get("_learning_context") or {}
    if learning:
        metrics = learning.get("quality_metrics") or {}
        meta["learning_context_stats"] = {
            "plans_used_for_learning": metrics.get("plans_used_for_learning", 0),
            "similar_plans_used": metrics.get("similar_plans_used", 0),
            "similar_profile_alignment_score": metrics.get("similar_profile_alignment_score"),
        }

    meta["context_source"] = "services"
    meta["student_id"] = student_id
    meta["assessment_id"] = assessment_id
    meta["measurement_id"] = measurement_id
    return plan_dict, meta


def log_llm_call(db: Session, meta: dict[str, Any]) -> int | None:
    stmt = text("""
        INSERT INTO llm_calls (
          correlation_id, route, provider, model, prompt_hash, prompt_len,
          resp_len, duration_ms, error, resp_raw,
          student_id, assessment_id, measurement_id
        )
        VALUES (:cid, :route, :prov, :model, :ph, :pl, :rl, :dur, :err, :raw, :sid, :aid, :mid)
        RETURNING id;
    """)
    raw = meta.get("resp_raw", "")
    if len(raw) > 5000:
        raw = raw[:5000]
    params = {
        "cid": meta.get("correlation_id"),
        "route": meta.get("route", "/llm/generate-plan"),
        "prov": meta.get("provider", "groq"),
        "model": meta.get("model", ""),
        "ph": meta.get("prompt_hash"),
        "pl": meta.get("prompt_len"),
        "rl": meta.get("resp_len"),
        "dur": meta.get("duration_ms"),
        "err": meta.get("error"),
        "raw": raw,
        "sid": meta.get("student_id"),
        "aid": meta.get("assessment_id"),
        "mid": meta.get("measurement_id"),
    }
    try:
        row = db.execute(stmt, params).mappings().one()
        db.commit()
        return row["id"]
    except Exception:
        db.rollback()
        return None
