from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def select_plan_fk_state(db: Session, student_id: int, assessment_id: int, measurement_id: int):
    return db.execute(text("""
        SELECT
          (SELECT student_id FROM assessments  WHERE id = :aid) AS a_sid,
          (SELECT student_id FROM measurements WHERE id = :mid) AS m_sid,
          (SELECT 1          FROM students     WHERE id = :sid) AS s_ok
    """), {"sid": student_id, "aid": assessment_id, "mid": measurement_id}).mappings().one()


def upsert_plan_comparison(
    db: Session,
    plan_id: int,
    llm_json: str,
    edited_json: str,
    similarity: float,
    comparison_json: str,
) -> None:
    db.execute(text("""
        INSERT INTO plan_llm_comparisons (
            plan_id, llm_plan_json, edited_plan_json, similarity_score, comparison_json, updated_at
        )
        VALUES (:pid, :llm_json, :edited_json, :similarity, :comparison_json, CURRENT_TIMESTAMP)
        ON CONFLICT (plan_id)
        DO UPDATE SET
            llm_plan_json = EXCLUDED.llm_plan_json,
            edited_plan_json = EXCLUDED.edited_plan_json,
            similarity_score = EXCLUDED.similarity_score,
            comparison_json = EXCLUDED.comparison_json,
            updated_at = CURRENT_TIMESTAMP;
    """), {
        "pid": plan_id,
        "llm_json": llm_json,
        "edited_json": edited_json,
        "similarity": similarity,
        "comparison_json": comparison_json,
    })


def set_current_plan(db: Session, student_id: int, plan_id: int) -> None:
    db.execute(text("""
        INSERT INTO student_current_plans (student_id, plan_id, assigned_at, updated_at)
        VALUES (:sid, :pid, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (student_id)
        DO UPDATE SET
            plan_id = EXCLUDED.plan_id,
            updated_at = CURRENT_TIMESTAMP;
    """), {"sid": student_id, "pid": plan_id})


def select_current_plan_pointer(db: Session, student_id: int):
    return db.execute(text("""
        SELECT plan_id
        FROM student_current_plans
        WHERE student_id = :sid;
    """), {"sid": student_id}).mappings().one_or_none()


def delete_current_plan_pointer(db: Session, student_id: int) -> None:
    db.execute(text("DELETE FROM student_current_plans WHERE student_id = :sid;"), {"sid": student_id})


def select_replacement_plan(db: Session, student_id: int, excluded_plan_id: int):
    return db.execute(text("""
        SELECT id
        FROM plans
        WHERE student_id = :sid AND id <> :pid
        ORDER BY updated_at DESC NULLS LAST, created_at DESC, id DESC
        LIMIT 1;
    """), {"sid": student_id, "pid": excluded_plan_id}).mappings().one_or_none()


def insert_plan(
    db: Session,
    student_id: int,
    assessment_id: int,
    measurement_id: int,
    generated_plan_json: str,
    plan_json: str,
    llm_call_id: int | None,
):
    return db.execute(text("""
        INSERT INTO plans (
            student_id, assessment_id, measurement_id, generated_plan_json,
            plan_json, llm_call_id, edit_count, updated_at
        )
        VALUES (:sid, :aid, :mid, :gen_json, :pjson, :llm_id, 0, CURRENT_TIMESTAMP)
        RETURNING id, student_id, assessment_id, measurement_id, generated_plan_json, plan_json,
                  llm_call_id, edit_count, created_at, updated_at;
    """), {
        "sid": student_id,
        "aid": assessment_id,
        "mid": measurement_id,
        "gen_json": generated_plan_json,
        "pjson": plan_json,
        "llm_id": llm_call_id,
    }).mappings().one()


def insert_plan_version(db: Session, plan_id: int, version_number: int, source: str, plan_json: str) -> None:
    db.execute(text("""
        INSERT INTO plan_versions (plan_id, version_number, source, plan_json)
        VALUES (:pid, :vnum, :src, :pjson);
    """), {"pid": plan_id, "vnum": version_number, "src": source, "pjson": plan_json})


def select_plan_state(db: Session, plan_id: int):
    return db.execute(text("""
        SELECT generated_plan_json, plan_json, edit_count FROM plans WHERE id = :id;
    """), {"id": plan_id}).mappings().one_or_none()


def update_plan_payload(db: Session, plan_id: int, plan_json: str, edit_count: int):
    return db.execute(text("""
        UPDATE plans SET plan_json = :pjson, edit_count = :ec, updated_at = CURRENT_TIMESTAMP
        WHERE id = :id
        RETURNING id, student_id, assessment_id, measurement_id, generated_plan_json, plan_json,
                  llm_call_id, edit_count, created_at, updated_at;
    """), {"pjson": plan_json, "ec": edit_count, "id": plan_id}).mappings().one()


def select_next_plan_version_number(db: Session, plan_id: int):
    return db.execute(text("""
        SELECT COALESCE(MAX(version_number), 0) + 1 AS n
        FROM plan_versions
        WHERE plan_id = :pid;
    """), {"pid": plan_id}).mappings().one()


def select_plan_by_id(db: Session, plan_id: int):
    return db.execute(text("""
        SELECT id, student_id, assessment_id, measurement_id, generated_plan_json, plan_json,
               llm_call_id, edit_count, created_at, updated_at
        FROM plans WHERE id = :pid;
    """), {"pid": plan_id}).mappings().one_or_none()


def select_plans_by_student(db: Session, student_id: int):
    return db.execute(text("""
        SELECT id, student_id, assessment_id, measurement_id, generated_plan_json, plan_json,
               llm_call_id, edit_count, created_at, updated_at
        FROM plans WHERE student_id = :sid ORDER BY id DESC;
    """), {"sid": student_id}).mappings().all()


def select_current_plan_by_student(db: Session, student_id: int):
    return db.execute(text("""
        SELECT
            p.id,
            p.student_id,
            p.assessment_id,
            p.measurement_id,
            p.generated_plan_json,
            p.plan_json,
            p.llm_call_id,
            p.edit_count,
            p.created_at,
            p.updated_at
        FROM student_current_plans scp
        JOIN plans p ON p.id = scp.plan_id
        WHERE scp.student_id = :sid;
    """), {"sid": student_id}).mappings().one_or_none()


def select_plan_student_id(db: Session, plan_id: int):
    return db.execute(text("SELECT student_id FROM plans WHERE id = :id;"), {"id": plan_id}).mappings().one_or_none()


def delete_plan_by_id(db: Session, plan_id: int) -> int:
    return db.execute(text("DELETE FROM plans WHERE id = :id;"), {"id": plan_id}).rowcount
