# src/services/plan_service.py
from __future__ import annotations
import json
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException


def _validate_fks(
    db: Session,
    student_id: int,
    assessment_id: int,
    measurement_id: int,
) -> None:
    """Valida que assessment e measurement pertencem ao mesmo student."""
    row = db.execute(text("""
        SELECT
          (SELECT student_id FROM assessments  WHERE id = :aid) AS a_sid,
          (SELECT student_id FROM measurements WHERE id = :mid) AS m_sid,
          (SELECT 1          FROM students     WHERE id = :sid) AS s_ok
    """), {"sid": student_id, "aid": assessment_id, "mid": measurement_id}).mappings().one()
    if row["s_ok"] is None:
        raise HTTPException(status_code=400, detail="student_id inválido.")
    if row["a_sid"] is None or row["m_sid"] is None:
        raise HTTPException(status_code=400, detail="assessment_id ou measurement_id inválidos.")
    if row["a_sid"] != student_id or row["m_sid"] != student_id:
        raise HTTPException(status_code=400, detail="IDs não pertencem ao mesmo aluno.")


def _plan_blob(plan_meta: dict, items: list) -> dict:
    return {"plan_meta": plan_meta, "items": items}


def create_plan_from_llm(
    db: Session,
    student_id: int,
    assessment_id: int,
    measurement_id: int,
    plan_meta: dict,
    items: list,
    llm_call_id: int | None = None,
) -> dict[str, Any]:
    """
    Cria um novo plano vindo do LLM.
    Salva generated_plan_json e plan_json com o mesmo conteúdo inicial.
    Cria plan_version v0 como source='llm'.
    """
    _validate_fks(db, student_id, assessment_id, measurement_id)
    blob = _plan_blob(plan_meta, items)
    pjson = json.dumps(blob, ensure_ascii=False)

    stmt = text("""
        INSERT INTO plans (student_id, assessment_id, measurement_id, generated_plan_json, plan_json, llm_call_id, edit_count, updated_at)
        VALUES (:sid, :aid, :mid, :gen_json, :pjson, :llm_id, 0, CURRENT_TIMESTAMP)
        RETURNING id, student_id, assessment_id, measurement_id, generated_plan_json, plan_json,
                  llm_call_id, edit_count, created_at, updated_at;
    """)
    try:
        row = db.execute(stmt, {
            "sid": student_id, "aid": assessment_id, "mid": measurement_id,
            "gen_json": pjson, "pjson": pjson, "llm_id": llm_call_id
        }).mappings().one()
        plan_id = row["id"]
        db.execute(text("""
            INSERT INTO plan_versions (plan_id, version_number, source, plan_json)
            VALUES (:pid, 1, 'llm', :pjson);
        """), {"pid": plan_id, "pjson": pjson})
        db.commit()
        return dict(row)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Erro ao salvar plano.")


def create_plan(
    db: Session,
    student_id: int,
    assessment_id: int,
    measurement_id: int,
    plan_meta: dict,
    items: list,
    generated_plan_json: dict | None = None,
    llm_call_id: int | None = None,
) -> dict[str, Any]:
    """
    Cria um plano (compatível com fluxo antigo: JSON editado pelo professor).
    Se generated_plan_json for None, usa o blob atual como generated.
    Cria plan_version v1 como source='teacher'.
    """
    _validate_fks(db, student_id, assessment_id, measurement_id)
    blob = _plan_blob(plan_meta, items)
    pjson = json.dumps(blob, ensure_ascii=False)
    gen_json = json.dumps(generated_plan_json, ensure_ascii=False) if generated_plan_json else pjson

    stmt = text("""
        INSERT INTO plans (student_id, assessment_id, measurement_id, generated_plan_json, plan_json, llm_call_id, edit_count, updated_at)
        VALUES (:sid, :aid, :mid, :gen_json, :pjson, :llm_id, 0, CURRENT_TIMESTAMP)
        RETURNING id, student_id, assessment_id, measurement_id, generated_plan_json, plan_json,
                  llm_call_id, edit_count, created_at, updated_at;
    """)
    try:
        row = db.execute(stmt, {
            "sid": student_id, "aid": assessment_id, "mid": measurement_id,
            "gen_json": gen_json, "pjson": pjson, "llm_id": llm_call_id
        }).mappings().one()
        plan_id = row["id"]
        db.execute(text("""
            INSERT INTO plan_versions (plan_id, version_number, source, plan_json)
            VALUES (:pid, 1, 'teacher', :pjson);
        """), {"pid": plan_id, "pjson": pjson})
        db.commit()
        return dict(row)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Erro ao salvar plano.")


def update_plan(db: Session, plan_id: int, plan_meta: dict | None, items: list | None) -> dict[str, Any]:
    """
    Atualiza o plano com edições do professor.
    Incrementa edit_count e cria nova entrada em plan_versions.
    """
    row = db.execute(text("""
        SELECT plan_json, edit_count FROM plans WHERE id = :id;
    """), {"id": plan_id}).mappings().one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Plan not found")

    current = row["plan_json"]
    if isinstance(current, str):
        current = json.loads(current)
    edit_count = row["edit_count"] or 0

    if plan_meta is not None:
        current["plan_meta"] = {**current.get("plan_meta", {}), **plan_meta}
    if items is not None:
        current["items"] = items

    pjson = json.dumps(current, ensure_ascii=False)
    version_num = edit_count + 2  # v1 foi criação; próxima é v2, v3...

    stmt = text("""
        UPDATE plans SET plan_json = :pjson, edit_count = :ec, updated_at = CURRENT_TIMESTAMP
        WHERE id = :id
        RETURNING id, student_id, assessment_id, measurement_id, generated_plan_json, plan_json,
                  llm_call_id, edit_count, created_at, updated_at;
    """)
    try:
        db.execute(text("""
            INSERT INTO plan_versions (plan_id, version_number, source, plan_json)
            VALUES (:pid, :vnum, 'teacher', :pjson);
        """), {"pid": plan_id, "vnum": version_num, "pjson": pjson})
        row2 = db.execute(stmt, {"pjson": pjson, "ec": edit_count + 1, "id": plan_id}).mappings().one()
        db.commit()
        return dict(row2)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Erro ao atualizar plano.")


def create_plan_version(db: Session, plan_id: int, source: str, plan_json: dict) -> dict[str, Any]:
    """Registra uma nova versão manualmente (útil para sincronização)."""
    if source not in ("llm", "teacher"):
        raise HTTPException(status_code=400, detail="source deve ser 'llm' ou 'teacher'")
    pjson = json.dumps(plan_json, ensure_ascii=False) if isinstance(plan_json, dict) else plan_json
    row = db.execute(text("SELECT COALESCE(MAX(version_number), 0) + 1 AS n FROM plan_versions WHERE plan_id = :pid;"),
                     {"pid": plan_id}).mappings().one()
    vnum = row["n"]
    db.execute(text("""
        INSERT INTO plan_versions (plan_id, version_number, source, plan_json)
        VALUES (:pid, :vnum, :src, :pjson);
    """), {"pid": plan_id, "vnum": vnum, "src": source, "pjson": pjson})
    db.commit()
    return {"plan_id": plan_id, "version_number": vnum, "source": source}


def get_plan(db: Session, plan_id: int) -> dict[str, Any] | None:
    row = db.execute(text("""
        SELECT id, student_id, assessment_id, measurement_id, generated_plan_json, plan_json,
               llm_call_id, edit_count, created_at, updated_at
        FROM plans WHERE id = :pid;
    """), {"pid": plan_id}).mappings().one_or_none()
    return dict(row) if row else None


def get_student_plans(db: Session, student_id: int) -> list[dict[str, Any]]:
    rows = db.execute(text("""
        SELECT id, student_id, assessment_id, measurement_id, generated_plan_json, plan_json,
               llm_call_id, edit_count, created_at, updated_at
        FROM plans WHERE student_id = :sid ORDER BY id DESC;
    """), {"sid": student_id}).mappings().all()
    return [dict(r) for r in rows]


def delete_plan(db: Session, plan_id: int) -> bool:
    res = db.execute(text("DELETE FROM plans WHERE id = :id;"), {"id": plan_id})
    db.commit()
    return res.rowcount > 0
