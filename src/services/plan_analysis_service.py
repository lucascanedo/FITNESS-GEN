"""
Analise de diferencas entre versoes de planos para aprendizado do LLM.
O LLM nunca acessa o banco; o backend computa o contexto e injeta no prompt.
"""
from __future__ import annotations

import json
import unicodedata
from collections import Counter, defaultdict
from statistics import mean
from typing import Any

from sqlalchemy.orm import Session

from src.repositories import plan_analysis_repository


TRACKED_FIELDS = ("sets", "reps", "rest_s", "load_pct_1rm", "rpe", "tempo")


def _safe_json(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _normalize_text(value: Any) -> str:
    text_value = str(value or "").strip().lower()
    normalized = unicodedata.normalize("NFKD", text_value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _normalize_exercise_name(value: Any) -> str:
    collapsed = " ".join(_normalize_text(value).split())
    return collapsed


def _normalize_reps(value: Any) -> str:
    text_value = _normalize_text(value)
    if not text_value:
        return ""
    if "-" in text_value:
        left, _, right = text_value.partition("-")
        if left.isdigit() and right.isdigit():
            return f"{int(left)}-{int(right)}"
    return text_value


def _normalize_scalar(field: str, value: Any) -> Any:
    if field == "reps":
        return _normalize_reps(value)
    if isinstance(value, str):
        return value.strip()
    return value


def _normalize_item(item: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(item)
    normalized["week"] = int(item.get("week", 1) or 1)
    normalized["day"] = _normalize_text(item.get("day", ""))
    normalized["exercise_name"] = _normalize_exercise_name(item.get("exercise_name", ""))
    for field in TRACKED_FIELDS:
        normalized[field] = _normalize_scalar(field, normalized.get(field))
    return normalized


def _get_items_set(plan: dict[str, Any]) -> set[str]:
    items = plan.get("items") or []
    return {_item_key(it) for it in items}


def _get_split(plan: dict[str, Any]) -> str:
    meta = plan.get("plan_meta") or {}
    return str(meta.get("split", "")).strip()


def _item_key(item: dict[str, Any]) -> str:
    normalized = _normalize_item(item)
    return f"{normalized['week']}-{normalized['day']}-{normalized['exercise_name']}"


def _compare_items(orig: list[dict[str, Any]], final: list[dict[str, Any]]) -> dict[str, Any]:
    """Compara itens entre versao original e final com normalizacao leve."""
    orig_map = {_item_key(it): _normalize_item(it) for it in (orig or [])}
    final_map = {_item_key(it): _normalize_item(it) for it in (final or [])}
    added = [final_map[key] for key in final_map if key not in orig_map]
    removed = [orig_map[key] for key in orig_map if key not in final_map]
    changed = []
    for key, original_item in orig_map.items():
        final_item = final_map.get(key)
        if final_item is None or original_item == final_item:
            continue
        diff = {
            "key": key,
            "exercise_name": final_item.get("exercise_name") or original_item.get("exercise_name"),
            "week": final_item.get("week", original_item.get("week", 1)),
            "day": final_item.get("day", original_item.get("day", "")),
            "original": original_item,
            "final": final_item,
            "field_changes": {},
        }
        for field in TRACKED_FIELDS:
            if original_item.get(field) != final_item.get(field):
                diff["field_changes"][field] = {
                    "from": original_item.get(field),
                    "to": final_item.get(field),
                }
                diff[field] = diff["field_changes"][field]
        changed.append(diff)
    return {"added": added, "removed": removed, "changed": changed}


def calculate_plan_similarity(original_plan: dict[str, Any], final_plan: dict[str, Any]) -> float:
    """
    Similaridade simples 0..1 entre plano LLM e plano final.
    Combina sobreposicao de exercicios com aderencia dos campos mais sensiveis.
    """
    original_items = original_plan.get("items", []) or []
    final_items = final_plan.get("items", []) or []
    original_keys = _get_items_set(original_plan)
    final_keys = _get_items_set(final_plan)

    if not original_keys and not final_keys:
        return 1.0

    union_count = len(original_keys | final_keys) or 1
    item_overlap = len(original_keys & final_keys) / union_count

    original_map = {_item_key(item): _normalize_item(item) for item in original_items}
    final_map = {_item_key(item): _normalize_item(item) for item in final_items}
    common_keys = list(original_keys & final_keys)

    if not common_keys:
        field_similarity = 0.0
    else:
        matches = 0
        total = 0
        for key in common_keys:
            for field in TRACKED_FIELDS:
                total += 1
                if original_map[key].get(field) == final_map[key].get(field):
                    matches += 1
        field_similarity = matches / total if total else 0.0

    similarity = (item_overlap * 0.65) + (field_similarity * 0.35)
    return round(similarity, 4)


def build_plan_comparison_snapshot(
    plan_id: int,
    original_plan: dict[str, Any],
    final_plan: dict[str, Any],
) -> dict[str, Any]:
    """
    Estrutura persistivel da comparacao entre plano LLM e plano salvo.
    """
    diff = _compare_items(original_plan.get("items", []), final_plan.get("items", []))
    split_changed = _get_split(original_plan) != _get_split(final_plan)
    similarity = calculate_plan_similarity(original_plan, final_plan)
    total_edits = len(diff["added"]) + len(diff["removed"]) + len(diff["changed"])
    original_count = max(len(original_plan.get("items", [])), 1)
    return {
        "plan_id": plan_id,
        "llm_plan_json": original_plan,
        "edited_plan_json": final_plan,
        "similarity_score": similarity,
        "comparison_json": {
            "summary": {
                "additions_count": len(diff["added"]),
                "removals_count": len(diff["removed"]),
                "changes_count": len(diff["changed"]),
                "edit_ratio": round(total_edits / original_count, 3),
                "split_changed": split_changed,
                "original_split": _get_split(original_plan),
                "final_split": _get_split(final_plan),
            },
            "added_exercises": [item["exercise_name"] for item in diff["added"]],
            "removed_exercises": [item["exercise_name"] for item in diff["removed"]],
            "field_changes": [
                {
                    "exercise_name": change["exercise_name"],
                    "field_changes": change["field_changes"],
                }
                for change in diff["changed"]
            ],
        },
    }


def _json_to_tokens(value: Any) -> set[str]:
    parsed = _safe_json(value)
    if isinstance(parsed, dict):
        tokens: set[str] = set()
        for key, inner_value in parsed.items():
            tokens.add(_normalize_text(key))
            tokens |= _json_to_tokens(inner_value)
        return {token for token in tokens if token}
    if isinstance(parsed, list):
        tokens: set[str] = set()
        for item in parsed:
            tokens |= _json_to_tokens(item)
        return {token for token in tokens if token}
    normalized = _normalize_text(parsed)
    return {normalized} if normalized else set()


def _extract_profile_from_row(row: dict[str, Any]) -> dict[str, Any]:
    freq = row.get("freq_per_week")
    session_time = row.get("session_time_min")
    return {
        "goal_tokens": sorted(_json_to_tokens(row.get("objectives"))),
        "level": _normalize_text(row.get("level")),
        "restriction_tokens": sorted(_json_to_tokens(row.get("restrictions"))),
        "injury_tokens": sorted(_json_to_tokens(row.get("injuries"))),
        "freq_per_week": int(freq) if isinstance(freq, int) or str(freq).isdigit() else None,
        "session_time_min": int(session_time) if isinstance(session_time, int) or str(session_time).isdigit() else None,
    }


def _extract_profile_from_bundle(bundle: dict[str, Any] | None) -> dict[str, Any] | None:
    if not bundle:
        return None
    assessment = bundle.get("assessment") or {}
    return _extract_profile_from_row(assessment)


def _token_overlap_ratio(left: list[str], right: list[str]) -> float:
    left_set = {token for token in left if token}
    right_set = {token for token in right if token}
    if not left_set or not right_set:
        return 0.0
    return len(left_set & right_set) / len(left_set | right_set)


def _profile_similarity(target: dict[str, Any] | None, candidate: dict[str, Any]) -> float:
    if not target:
        return 0.0
    score = 0.0
    score += _token_overlap_ratio(target.get("goal_tokens", []), candidate.get("goal_tokens", [])) * 0.35
    score += _token_overlap_ratio(target.get("restriction_tokens", []), candidate.get("restriction_tokens", [])) * 0.2
    score += _token_overlap_ratio(target.get("injury_tokens", []), candidate.get("injury_tokens", [])) * 0.2
    if target.get("level") and target.get("level") == candidate.get("level"):
        score += 0.15
    target_freq = target.get("freq_per_week")
    candidate_freq = candidate.get("freq_per_week")
    if target_freq and candidate_freq:
        score += max(0.0, 0.05 - (abs(target_freq - candidate_freq) * 0.01))
    target_session = target.get("session_time_min")
    candidate_session = candidate.get("session_time_min")
    if target_session and candidate_session:
        score += max(0.0, 0.05 - (abs(target_session - candidate_session) / 300))
    return round(min(score, 1.0), 4)


def _split_transition(original_plan: dict[str, Any], final_plan: dict[str, Any]) -> str | None:
    original = _normalize_text(_get_split(original_plan))
    final = _normalize_text(_get_split(final_plan))
    if not original or not final or original == final:
        return None
    return f"{original}->{final}"


def _round_if_number(value: float | int | None) -> float | int | None:
    if isinstance(value, float):
        return round(value, 2)
    return value


def _average_numeric_delta(changes: list[dict[str, Any]], field: str) -> float | None:
    deltas = []
    for change in changes:
        field_change = change.get("field_changes", {}).get(field)
        if not field_change:
            continue
        before = field_change.get("from")
        after = field_change.get("to")
        if isinstance(before, (int, float)) and isinstance(after, (int, float)):
            deltas.append(after - before)
    return round(mean(deltas), 2) if deltas else None


def _summarize_patterns(patterns: list[dict[str, Any]]) -> dict[str, Any]:
    if not patterns:
        return {
            "plans_analyzed": 0,
            "plans_with_edits": 0,
            "avg_edit_ratio": 0.0,
            "top_added_exercises": [],
            "top_removed_exercises": [],
            "common_split_transitions": [],
            "field_adjustments": {},
            "profile_distribution": {},
        }

    added_counter = Counter()
    removed_counter = Counter()
    split_counter = Counter()
    level_counter = Counter()
    goal_counter = Counter()
    field_counter = Counter()

    changes_by_field: dict[str, list[dict[str, Any]]] = defaultdict(list)
    edit_ratios = []
    similarities = []

    for pattern in patterns:
        edit_ratios.append(pattern["edit_ratio"])
        similarities.append(pattern["similarity_score"])
        added_counter.update(pattern["added_exercises"])
        removed_counter.update(pattern["removed_exercises"])
        if pattern.get("split_transition"):
            split_counter.update([pattern["split_transition"]])
        profile = pattern.get("profile", {})
        if profile.get("level"):
            level_counter.update([profile["level"]])
        goal_counter.update(profile.get("goal_tokens", []))
        for change in pattern["changed_details"]:
            for field in change.get("field_changes", {}):
                field_counter.update([field])
                changes_by_field[field].append(change)

    field_adjustments = {}
    for field, field_changes in changes_by_field.items():
        field_adjustments[field] = {
            "count": len(field_changes),
            "avg_delta": _average_numeric_delta(field_changes, field),
        }

    return {
        "plans_analyzed": len(patterns),
        "plans_with_edits": sum(1 for pattern in patterns if pattern["has_edits"]),
        "avg_edit_ratio": round(mean(edit_ratios), 3),
        "avg_similarity_score": round(mean(similarities), 3),
        "top_added_exercises": [
            {"exercise_name": name, "count": count}
            for name, count in added_counter.most_common(5)
        ],
        "top_removed_exercises": [
            {"exercise_name": name, "count": count}
            for name, count in removed_counter.most_common(5)
        ],
        "common_split_transitions": [
            {"transition": transition, "count": count}
            for transition, count in split_counter.most_common(5)
        ],
        "field_adjustments": field_adjustments,
        "most_changed_fields": [
            {"field": field, "count": count}
            for field, count in field_counter.most_common(5)
        ],
        "profile_distribution": {
            "levels": dict(level_counter.most_common(5)),
            "goals": dict(goal_counter.most_common(8)),
        },
    }


def _build_guidance(summary: dict[str, Any], focus_patterns: list[dict[str, Any]]) -> list[str]:
    guidance: list[str] = []
    if summary["top_added_exercises"]:
        names = ", ".join(item["exercise_name"] for item in summary["top_added_exercises"][:3])
        guidance.append(f"O professor costuma adicionar: {names}.")
    if summary["top_removed_exercises"]:
        names = ", ".join(item["exercise_name"] for item in summary["top_removed_exercises"][:3])
        guidance.append(f"O professor costuma remover ou substituir: {names}.")
    for field in ("sets", "reps", "rest_s", "rpe", "tempo"):
        field_summary = summary["field_adjustments"].get(field)
        if not field_summary:
            continue
        avg_delta = field_summary.get("avg_delta")
        if avg_delta is None:
            guidance.append(f"O professor ajusta {field} com frequencia.")
            continue
        if avg_delta > 0:
            guidance.append(f"O professor tende a aumentar {field} em media {avg_delta}.")
        elif avg_delta < 0:
            guidance.append(f"O professor tende a reduzir {field} em media {abs(avg_delta)}.")
    if focus_patterns:
        best = focus_patterns[0]
        profile = best.get("profile", {})
        descriptors = []
        if profile.get("level"):
            descriptors.append(f"nivel {profile['level']}")
        if profile.get("goal_tokens"):
            descriptors.append(f"objetivos {', '.join(profile['goal_tokens'][:3])}")
        if descriptors:
            guidance.append(
                "O historico mais parecido com o caso atual vem de alunos com "
                + " e ".join(descriptors)
                + "."
            )
    return guidance[:8]


def _build_examples(patterns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    examples = []
    for pattern in patterns[:3]:
        example = {
            "plan_id": pattern["plan_id"],
            "profile_similarity": pattern["profile_similarity"],
            "added_exercises": pattern["added_exercises"][:3],
            "removed_exercises": pattern["removed_exercises"][:3],
            "field_changes": [],
        }
        for change in pattern["changed_details"][:3]:
            example["field_changes"].append(
                {
                    "exercise_name": change["exercise_name"],
                    "changes": change["field_changes"],
                }
            )
        examples.append(example)
    return examples


def _fetch_plan_rows(db: Session, student_id: int | None = None) -> list[dict[str, Any]]:
    rows = plan_analysis_repository.select_plan_rows_for_analysis(db, student_id)
    return [dict(row) for row in rows]


def _pattern_from_row(row: dict[str, Any], target_profile: dict[str, Any] | None = None) -> dict[str, Any]:
    original_plan = _safe_json(row["generated_plan_json"]) or {}
    final_plan = _safe_json(row["plan_json"]) or {}
    diff = _compare_items(original_plan.get("items", []), final_plan.get("items", []))
    original_count = max(len(original_plan.get("items", [])), 1)
    total_edits = len(diff["added"]) + len(diff["removed"]) + len(diff["changed"])
    profile = _extract_profile_from_row(row)
    comparison_json = _safe_json(row.get("comparison_json")) or {}
    comparison_summary = comparison_json.get("summary", {}) if isinstance(comparison_json, dict) else {}
    similarity_score = row.get("similarity_score")
    if similarity_score is None:
        similarity_score = calculate_plan_similarity(original_plan, final_plan)
    return {
        "plan_id": row["id"],
        "student_id": row["student_id"],
        "profile": profile,
        "profile_similarity": _profile_similarity(target_profile, profile),
        "additions_count": len(diff["added"]),
        "removals_count": len(diff["removed"]),
        "changes_count": len(diff["changed"]),
        "edit_ratio": round(total_edits / original_count, 3),
        "edit_count": row.get("edit_count") or 0,
        "has_edits": total_edits > 0,
        "similarity_score": float(similarity_score),
        "added_exercises": [item["exercise_name"] for item in diff["added"]],
        "removed_exercises": [item["exercise_name"] for item in diff["removed"]],
        "changed_details": diff["changed"],
        "split_transition": _split_transition(original_plan, final_plan),
        "comparison_summary": comparison_summary,
    }


def analyze_plan_differences(db: Session, plan_id: int) -> dict[str, Any]:
    """
    Compara versao original (AI) com versao final (professor) e versoes intermediarias.
    Retorna exercicios adicionados/removidos, mudancas em sets/reps/load/rest,
    mudanca de split e um resumo.
    """
    plan = plan_analysis_repository.select_plan_for_difference_analysis(db, plan_id)
    if not plan:
        return {"error": "Plan not found"}

    original_plan = _safe_json(plan["generated_plan_json"] or plan["plan_json"]) or {}
    final_plan = _safe_json(plan["plan_json"]) or {}

    split_changed = _get_split(original_plan) != _get_split(final_plan)
    items_diff = _compare_items(original_plan.get("items", []), final_plan.get("items", []))
    original_set = _get_items_set(original_plan)
    final_set = _get_items_set(final_plan)
    exercises_added = list(final_set - original_set)
    exercises_removed = list(original_set - final_set)
    total_edits = len(exercises_added) + len(exercises_removed) + len(items_diff["changed"])
    edit_ratio = round(total_edits / max(len(original_plan.get("items", [])), 1), 3)

    versions = plan_analysis_repository.select_plan_versions(db, plan_id)

    summary_parts = []
    if exercises_removed:
        summary_parts.append(f"Removeu {len(exercises_removed)} exercicio(s).")
    if exercises_added:
        summary_parts.append(f"Adicionou {len(exercises_added)} exercicio(s).")
    if items_diff["changed"]:
        summary_parts.append(f"Alterou {len(items_diff['changed'])} exercicio(s) em volume/carga.")
    if split_changed:
        summary_parts.append("Alterou o split do plano.")
    semantic_summary = " ".join(summary_parts) if summary_parts else "Nenhuma alteracao significativa."

    return {
        "plan_id": plan_id,
        "exercises_added": exercises_added,
        "exercises_removed": exercises_removed,
        "sets_reps_load_rest_changes": [change for change in items_diff["changed"]],
        "split_changed": split_changed,
        "original_split": _get_split(original_plan),
        "final_split": _get_split(final_plan),
        "semantic_summary": semantic_summary,
        "edit_count": plan["edit_count"],
        "edit_ratio": edit_ratio,
        "intermediate_versions_count": len(versions) - 2 if len(versions) > 2 else 0,
    }


def get_professor_edit_patterns(
    db: Session,
    student_id: int | None = None,
    target_bundle: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Agrega padroes de edicao do professor.
    Se houver target_bundle, calcula similaridade de perfil para priorizar casos parecidos.
    """
    target_profile = _extract_profile_from_bundle(target_bundle)
    rows = _fetch_plan_rows(db, student_id)
    patterns = [_pattern_from_row(row, target_profile) for row in rows]
    patterns = [pattern for pattern in patterns if pattern["has_edits"]]
    return sorted(
        patterns,
        key=lambda pattern: (pattern["profile_similarity"], pattern["edit_ratio"], pattern["plan_id"]),
        reverse=True,
    )


def build_llm_learning_context(
    db: Session,
    student_id: int | None = None,
    target_bundle: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Monta o contexto de aprendizado para injetar no prompt do LLM.
    Retorna apenas padroes agregados e exemplos anonimizados.
    """
    patterns = get_professor_edit_patterns(db, student_id=student_id, target_bundle=target_bundle)
    if not patterns:
        return {}

    similar_patterns = [pattern for pattern in patterns if pattern["profile_similarity"] >= 0.35][:5]
    focus_patterns = similar_patterns or patterns[:5]
    summary = _summarize_patterns(patterns)
    focus_summary = _summarize_patterns(focus_patterns)
    target_profile = _extract_profile_from_bundle(target_bundle)

    return {
        "summary": summary,
        "profile_focus": {
            "target_profile": target_profile,
            "matched_plans": len(focus_patterns),
            "avg_profile_similarity": round(
                mean(pattern["profile_similarity"] for pattern in focus_patterns),
                3,
            ) if focus_patterns else 0.0,
            "summary": focus_summary,
        },
        "prompt_guidance": _build_guidance(summary, focus_patterns),
        "examples": _build_examples(focus_patterns),
        "quality_metrics": {
            "historical_alignment_score": _round_if_number(summary["avg_similarity_score"]),
            "similar_profile_alignment_score": _round_if_number(focus_summary["avg_similarity_score"]),
            "plans_used_for_learning": len(patterns),
            "similar_plans_used": len(focus_patterns),
        },
    }


def get_professor_learning_diagnostics(
    db: Session,
    student_id: int | None = None,
    target_bundle: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Exponibiliza metricas simples para auditar qualidade do aprendizado.
    """
    context = build_llm_learning_context(db, student_id=student_id, target_bundle=target_bundle)
    if not context:
        return {
            "summary": {
                "plans_analyzed": 0,
                "plans_with_edits": 0,
                "avg_edit_ratio": 0.0,
                "avg_similarity_score": 0.0,
            },
            "quality_metrics": {
                "historical_alignment_score": 0.0,
                "similar_profile_alignment_score": 0.0,
                "plans_used_for_learning": 0,
                "similar_plans_used": 0,
            },
            "prompt_guidance": [],
        }
    return {
        "summary": context["summary"],
        "profile_focus": context["profile_focus"],
        "quality_metrics": context["quality_metrics"],
        "prompt_guidance": context["prompt_guidance"],
    }


def get_plan_comparison(db: Session, plan_id: int) -> dict[str, Any] | None:
    row = plan_analysis_repository.select_plan_comparison_by_plan_id(db, plan_id)
    return dict(row) if row else None


def build_student_plan_mcp_context(db: Session, student_id: int) -> dict[str, Any]:
    """
    Payload compacto e deterministico para uso via tool/contexto da IA.
    Evita enviar historico bruto inteiro no prompt.
    """
    current_plan_row = plan_analysis_repository.select_current_plan_context_row(db, student_id)

    current_plan = None
    comparison = None
    if current_plan_row:
        current_plan = {
            "plan_id": current_plan_row["id"],
            "assessment_id": current_plan_row["assessment_id"],
            "measurement_id": current_plan_row["measurement_id"],
            "edit_count": current_plan_row["edit_count"] or 0,
            "updated_at": current_plan_row["updated_at"],
            "plan_json": _safe_json(current_plan_row["plan_json"]) or {},
        }
        comparison = get_plan_comparison(db, current_plan_row["id"])

    learning = get_professor_learning_diagnostics(db, student_id=student_id)
    return {
        "student_id": student_id,
        "current_plan": current_plan,
        "current_plan_comparison": comparison,
        "learning_diagnostics": learning,
    }
