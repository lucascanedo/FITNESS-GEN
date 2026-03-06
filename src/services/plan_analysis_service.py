# src/services/plan_analysis_service.py
"""
Análise de diferenças entre versões de planos para aprendizado do LLM.
O LLM nunca acessa o banco; o backend computa o contexto e injeta no prompt.
"""
from __future__ import annotations
import json
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import text


def _get_items_set(plan: dict) -> set[str]:
    """Retorna um set de identificadores de exercícios (week-day-name)."""
    items = plan.get("items") or []
    s = set()
    for it in items:
        week = it.get("week", 1)
        day = str(it.get("day", ""))
        name = str(it.get("exercise_name", "")).strip()
        s.add(f"{week}-{day}-{name}")
    return s


def _get_split(plan: dict) -> str:
    meta = plan.get("plan_meta") or {}
    return str(meta.get("split", ""))


def _item_key(it: dict) -> str:
    return f"{it.get('week',1)}-{it.get('day','')}-{it.get('exercise_name','')}"


def _compare_items(orig: list, final: list) -> dict[str, Any]:
    """Compara itens entre versão original e final."""
    orig_map = {_item_key(it): it for it in (orig or [])}
    final_map = {_item_key(it): it for it in (final or [])}
    added = [final_map[k] for k in final_map if k not in orig_map]
    removed = [orig_map[k] for k in orig_map if k not in final_map]
    changed = []
    for k in orig_map:
        if k in final_map:
            o, f = orig_map[k], final_map[k]
            if o != f:
                diff = {"key": k, "original": o, "final": f}
                for field in ("sets", "reps", "rest_s", "load_pct_1rm", "rpe", "tempo"):
                    if o.get(field) != f.get(field):
                        diff[field] = {"from": o.get(field), "to": f.get(field)}
                changed.append(diff)
    return {"added": added, "removed": removed, "changed": changed}


def analyze_plan_differences(db: Session, plan_id: int) -> dict[str, Any]:
    """
    Compara versão original (AI) com versão final (professor) e versões intermediárias.
    Retorna: exercícios adicionados/removidos, mudanças em sets/reps/load/rest, mudança de split, resumo.
    """
    plan = db.execute(text("""
        SELECT generated_plan_json, plan_json, edit_count
        FROM plans WHERE id = :pid;
    """), {"pid": plan_id}).mappings().one_or_none()
    if not plan:
        return {"error": "Plan not found"}

    orig = plan["generated_plan_json"] or plan["plan_json"]
    final = plan["plan_json"]
    if isinstance(orig, str):
        orig = json.loads(orig) if orig else {}
    if isinstance(final, str):
        final = json.loads(final) if final else {}

    split_changed = _get_split(orig) != _get_split(final)
    items_diff = _compare_items(orig.get("items", []), final.get("items", []))
    orig_set = _get_items_set(orig)
    final_set = _get_items_set(final)
    exercises_added = list(final_set - orig_set)
    exercises_removed = list(orig_set - final_set)

    versions = db.execute(text("""
        SELECT version_number, source, plan_json, created_at
        FROM plan_versions WHERE plan_id = :pid ORDER BY version_number;
    """), {"pid": plan_id}).mappings().all()

    summary_parts = []
    if exercises_removed:
        summary_parts.append(f"Removeu {len(exercises_removed)} exercício(s).")
    if exercises_added:
        summary_parts.append(f"Adicionou {len(exercises_added)} exercício(s).")
    if items_diff["changed"]:
        summary_parts.append(f"Alterou {len(items_diff['changed'])} exercício(s) em volume/carga.")
    if split_changed:
        summary_parts.append("Alterou o split do plano.")
    semantic_summary = " ".join(summary_parts) if summary_parts else "Nenhuma alteração significativa."

    return {
        "plan_id": plan_id,
        "exercises_added": exercises_added,
        "exercises_removed": exercises_removed,
        "sets_reps_load_rest_changes": [c for c in items_diff["changed"]],
        "split_changed": split_changed,
        "original_split": _get_split(orig),
        "final_split": _get_split(final),
        "semantic_summary": semantic_summary,
        "edit_count": plan["edit_count"],
        "intermediate_versions_count": len(versions) - 2 if len(versions) > 2 else 0,
    }


def get_professor_edit_patterns(db: Session, student_id: int | None = None) -> list[dict[str, Any]]:
    """
    Agrega padrões de edição do professor (o que ele costuma alterar).
    Se student_id for None, agrega de todos os alunos.
    """
    sql = """
        SELECT p.id, p.student_id, p.generated_plan_json, p.plan_json
        FROM plans p
        WHERE p.generated_plan_json IS NOT NULL AND p.plan_json IS NOT NULL
    """
    params: dict[str, Any] = {}
    if student_id is not None:
        sql += " AND p.student_id = :sid"
        params["sid"] = student_id
    rows = db.execute(text(sql), params).mappings().all()

    patterns = []
    for row in rows:
        orig = row["generated_plan_json"]
        final = row["plan_json"]
        if isinstance(orig, str):
            orig = json.loads(orig) if orig else {}
        if isinstance(final, str):
            final = json.loads(final) if final else {}
        diff = _compare_items(orig.get("items", []), final.get("items", []))
        if diff["added"] or diff["removed"] or diff["changed"]:
            patterns.append({
                "plan_id": row["id"],
                "student_id": row["student_id"],
                "additions_count": len(diff["added"]),
                "removals_count": len(diff["removed"]),
                "changes_count": len(diff["changed"]),
            })
    return patterns


def build_llm_learning_context(db: Session, student_id: int | None = None) -> str:
    """
    Monta o contexto de aprendizado para injetar no prompt do LLM.
    Baseado no histórico de edições do professor.
    Não retorna dados sensíveis; apenas padrões de comportamento.
    """
    patterns = get_professor_edit_patterns(db, student_id)
    if not patterns:
        return ""

    parts = ["### Histórico de edições do treinador (use como referência para futuros planos):\n"]
    for p in patterns[:10]:
        parts.append(
            f"- Plano {p['plan_id']}: "
            f"+{p['additions_count']} exercícios, -{p['removals_count']}, "
            f"{p['changes_count']} alterações de volume/carga."
        )
    return "\n".join(parts)
