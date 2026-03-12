from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def select_plan_rows_for_analysis(db: Session, student_id: int | None = None):
    params: dict[str, Any] = {}
    comparison_sql = """
        SELECT
            p.id,
            p.student_id,
            plc.llm_plan_json AS generated_plan_json,
            plc.edited_plan_json AS plan_json,
            p.edit_count,
            a.objectives,
            a.level,
            a.restrictions,
            a.injuries,
            a.freq_per_week,
            a.session_time_min,
            plc.similarity_score,
            plc.comparison_json
        FROM plan_llm_comparisons plc
        JOIN plans p ON p.id = plc.plan_id
        JOIN assessments a ON a.id = p.assessment_id
        WHERE plc.llm_plan_json IS NOT NULL
          AND plc.edited_plan_json IS NOT NULL
    """
    if student_id is not None:
        comparison_sql += " AND p.student_id = :sid"
        params["sid"] = student_id
    rows = db.execute(text(comparison_sql), params).mappings().all()
    if rows:
        return rows

    fallback_sql = """
        SELECT
            p.id,
            p.student_id,
            p.generated_plan_json,
            p.plan_json,
            p.edit_count,
            a.objectives,
            a.level,
            a.restrictions,
            a.injuries,
            a.freq_per_week,
            a.session_time_min,
            NULL::NUMERIC AS similarity_score,
            NULL::JSONB AS comparison_json
        FROM plans p
        JOIN assessments a ON a.id = p.assessment_id
        WHERE p.generated_plan_json IS NOT NULL
          AND p.plan_json IS NOT NULL
    """
    if student_id is not None:
        fallback_sql += " AND p.student_id = :sid"
    return db.execute(text(fallback_sql), params).mappings().all()


def select_plan_for_difference_analysis(db: Session, plan_id: int):
    return db.execute(text("""
        SELECT generated_plan_json, plan_json, edit_count
        FROM plans WHERE id = :pid;
    """), {"pid": plan_id}).mappings().one_or_none()


def select_plan_versions(db: Session, plan_id: int):
    return db.execute(text("""
        SELECT version_number, source, plan_json, created_at
        FROM plan_versions WHERE plan_id = :pid ORDER BY version_number;
    """), {"pid": plan_id}).mappings().all()


def select_plan_comparison_by_plan_id(db: Session, plan_id: int):
    return db.execute(text("""
        SELECT
            id,
            plan_id,
            llm_plan_json,
            edited_plan_json,
            similarity_score,
            comparison_json,
            created_at,
            updated_at
        FROM plan_llm_comparisons
        WHERE plan_id = :pid;
    """), {"pid": plan_id}).mappings().one_or_none()


def select_current_plan_context_row(db: Session, student_id: int):
    return db.execute(text("""
        SELECT
            p.id,
            p.assessment_id,
            p.measurement_id,
            p.plan_json,
            p.generated_plan_json,
            p.edit_count,
            p.updated_at
        FROM student_current_plans scp
        JOIN plans p ON p.id = scp.plan_id
        WHERE scp.student_id = :sid;
    """), {"sid": student_id}).mappings().one_or_none()
