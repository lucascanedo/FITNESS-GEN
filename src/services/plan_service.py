# src/services/plan_service.py
from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.repositories import plan_repository
from src.services.plan_analysis_service import build_plan_comparison_snapshot


def _validate_fks(
    db: Session,
    student_id: int,
    assessment_id: int,
    measurement_id: int,
) -> None:
    row = plan_repository.select_plan_fk_state(db, student_id, assessment_id, measurement_id)
    if row["s_ok"] is None:
        raise HTTPException(status_code=400, detail="student_id invÃ¡lido.")
    if row["a_sid"] is None or row["m_sid"] is None:
        raise HTTPException(status_code=400, detail="assessment_id ou measurement_id invÃ¡lidos.")
    if row["a_sid"] != student_id or row["m_sid"] != student_id:
        raise HTTPException(status_code=400, detail="IDs nÃ£o pertencem ao mesmo aluno.")


def _plan_blob(plan_meta: dict, items: list) -> dict:
    return {"plan_meta": plan_meta, "items": items}


def _sync_plan_comparison(
    db: Session,
    plan_id: int,
    generated_plan: dict[str, Any],
    edited_plan: dict[str, Any],
) -> None:
    snapshot = build_plan_comparison_snapshot(plan_id, generated_plan, edited_plan)
    plan_repository.upsert_plan_comparison(
        db=db,
        plan_id=plan_id,
        llm_json=json.dumps(snapshot["llm_plan_json"], ensure_ascii=False),
        edited_json=json.dumps(snapshot["edited_plan_json"], ensure_ascii=False),
        similarity=snapshot["similarity_score"],
        comparison_json=json.dumps(snapshot["comparison_json"], ensure_ascii=False),
    )


def _set_current_plan(db: Session, student_id: int, plan_id: int) -> None:
    plan_repository.set_current_plan(db, student_id, plan_id)


def _reassign_current_plan_after_delete(db: Session, student_id: int, deleted_plan_id: int) -> None:
    current_row = plan_repository.select_current_plan_pointer(db, student_id)
    if current_row is None or current_row["plan_id"] != deleted_plan_id:
        return

    replacement = plan_repository.select_replacement_plan(db, student_id, deleted_plan_id)
    if replacement is None:
        plan_repository.delete_current_plan_pointer(db, student_id)
        return

    _set_current_plan(db, student_id, replacement["id"])


def create_plan_from_llm(
    db: Session,
    student_id: int,
    assessment_id: int,
    measurement_id: int,
    plan_meta: dict,
    items: list,
    llm_call_id: int | None = None,
) -> dict[str, Any]:
    _validate_fks(db, student_id, assessment_id, measurement_id)
    blob = _plan_blob(plan_meta, items)
    pjson = json.dumps(blob, ensure_ascii=False)

    try:
        row = plan_repository.insert_plan(
            db=db,
            student_id=student_id,
            assessment_id=assessment_id,
            measurement_id=measurement_id,
            generated_plan_json=pjson,
            plan_json=pjson,
            llm_call_id=llm_call_id,
        )
        plan_id = row["id"]
        plan_repository.insert_plan_version(db, plan_id, 1, "llm", pjson)
        _sync_plan_comparison(db, plan_id, blob, blob)
        _set_current_plan(db, student_id, plan_id)
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
    _validate_fks(db, student_id, assessment_id, measurement_id)
    blob = _plan_blob(plan_meta, items)
    pjson = json.dumps(blob, ensure_ascii=False)
    gen_json = json.dumps(generated_plan_json, ensure_ascii=False) if generated_plan_json else pjson

    try:
        row = plan_repository.insert_plan(
            db=db,
            student_id=student_id,
            assessment_id=assessment_id,
            measurement_id=measurement_id,
            generated_plan_json=gen_json,
            plan_json=pjson,
            llm_call_id=llm_call_id,
        )
        plan_id = row["id"]
        plan_repository.insert_plan_version(db, plan_id, 1, "teacher", pjson)
        _sync_plan_comparison(db, plan_id, json.loads(gen_json), blob)
        _set_current_plan(db, student_id, plan_id)
        db.commit()
        return dict(row)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Erro ao salvar plano.")


def update_plan(db: Session, plan_id: int, plan_meta: dict | None, items: list | None) -> dict[str, Any]:
    row = plan_repository.select_plan_state(db, plan_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Plan not found")

    generated_plan = row["generated_plan_json"] or row["plan_json"]
    current = row["plan_json"]
    if isinstance(generated_plan, str):
        generated_plan = json.loads(generated_plan)
    if isinstance(current, str):
        current = json.loads(current)
    edit_count = row["edit_count"] or 0

    if plan_meta is not None:
        current["plan_meta"] = {**current.get("plan_meta", {}), **plan_meta}
    if items is not None:
        current["items"] = items

    pjson = json.dumps(current, ensure_ascii=False)
    version_num = edit_count + 2

    try:
        plan_repository.insert_plan_version(db, plan_id, version_num, "teacher", pjson)
        row2 = plan_repository.update_plan_payload(db, plan_id, pjson, edit_count + 1)
        _sync_plan_comparison(db, plan_id, generated_plan, current)
        _set_current_plan(db, row2["student_id"], plan_id)
        db.commit()
        return dict(row2)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Erro ao atualizar plano.")


def create_plan_version(db: Session, plan_id: int, source: str, plan_json: dict) -> dict[str, Any]:
    if source not in ("llm", "teacher"):
        raise HTTPException(status_code=400, detail="source deve ser 'llm' ou 'teacher'")
    pjson = json.dumps(plan_json, ensure_ascii=False) if isinstance(plan_json, dict) else plan_json
    row = plan_repository.select_next_plan_version_number(db, plan_id)
    vnum = row["n"]
    plan_repository.insert_plan_version(db, plan_id, vnum, source, pjson)
    db.commit()
    return {"plan_id": plan_id, "version_number": vnum, "source": source}


def get_plan(db: Session, plan_id: int) -> dict[str, Any] | None:
    row = plan_repository.select_plan_by_id(db, plan_id)
    return dict(row) if row else None


def get_student_plans(db: Session, student_id: int) -> list[dict[str, Any]]:
    rows = plan_repository.select_plans_by_student(db, student_id)
    return [dict(r) for r in rows]


def get_current_student_plan(db: Session, student_id: int) -> dict[str, Any] | None:
    row = plan_repository.select_current_plan_by_student(db, student_id)
    return dict(row) if row else None


def delete_plan(db: Session, plan_id: int) -> bool:
    row = plan_repository.select_plan_student_id(db, plan_id)
    if row is None:
        return False
    rowcount = plan_repository.delete_plan_by_id(db, plan_id)
    _reassign_current_plan_after_delete(db, row["student_id"], plan_id)
    db.commit()
    return rowcount > 0
