# src/services/llm_service.py
"""
Orquestração do LLM: construção de contexto, geração e log.
A lógica de negócio permanece nos services; o LLM apenas gera texto.
"""
from __future__ import annotations
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import text

from src.IA.llm_helpers import get_llm_bundle
from src.IA.llm_generator import LLMGenerator
from src.services.plan_analysis_service import build_llm_learning_context


def build_generation_context(
    db: Session,
    student_id: int,
    assessment_id: int,
    measurement_id: int,
    include_learning: bool = True,
) -> dict[str, Any]:
    """
    Monta o bundle completo para geração (student, assessment, measurement).
    Se include_learning=True, adiciona contexto de edições do professor.
    """
    bundle = get_llm_bundle(
        db=db,
        student_id=student_id,
        assessment_id=assessment_id,
        measurement_id=measurement_id,
        enforce_snapshot_match=False,
    )
    if include_learning:
        learning = build_llm_learning_context(db, student_id)
        if learning:
            bundle["_learning_context"] = learning
    return bundle


def generate_plan_with_learning_context(
    db: Session,
    student_id: int,
    assessment_id: int,
    measurement_id: int,
    correlation_id: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Gera um plano via LLM com contexto de aprendizado injetado.
    Retorna (plan_dict, meta) para o chamador persistir e logar.
    """
    bundle = build_generation_context(
        db, student_id, assessment_id, measurement_id, include_learning=True
    )
    llm = LLMGenerator()
    plan_dict, meta = llm.generate_plan(bundle, correlation_id=correlation_id)
    meta["student_id"] = student_id
    meta["assessment_id"] = assessment_id
    meta["measurement_id"] = measurement_id
    return plan_dict, meta


def log_llm_call(db: Session, meta: dict[str, Any]) -> int | None:
    """
    Insere registro em llm_calls e retorna o id.
    """
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
