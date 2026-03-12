import unittest

from src.services.llm_context_service import sanitize_bundle_for_prompt
from src.services.plan_analysis_service import (
    _compare_items,
    analyze_plan_differences,
    build_student_plan_mcp_context,
    build_llm_learning_context,
    build_plan_comparison_snapshot,
    calculate_plan_similarity,
)


class FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def mappings(self):
        return self

    def all(self):
        return self.rows

    def one_or_none(self):
        return self.rows[0] if self.rows else None


class FakeSession:
    def __init__(self, query_map):
        self.query_map = query_map

    def execute(self, stmt, params=None):
        sql = str(stmt)
        for fragment, rows in sorted(self.query_map.items(), key=lambda item: len(item[0]), reverse=True):
            if fragment in sql:
                return FakeResult(rows)
        raise AssertionError(f"Unexpected query: {sql}")


class LearningContextTests(unittest.TestCase):
    def test_compare_items_normalizes_names_and_reps(self):
        original = [
            {
                "week": 1,
                "day": "A",
                "exercise_name": "Agachamento Livre",
                "sets": 3,
                "reps": "10 - 12",
                "rest_s": 60,
                "tempo": "2-0-2",
            }
        ]
        final = [
            {
                "week": 1,
                "day": "a",
                "exercise_name": "agachamento livre",
                "sets": 4,
                "reps": "10-12",
                "rest_s": 75,
                "tempo": "2-0-2",
            }
        ]

        diff = _compare_items(original, final)

        self.assertEqual(diff["added"], [])
        self.assertEqual(diff["removed"], [])
        self.assertEqual(len(diff["changed"]), 1)
        self.assertEqual(diff["changed"][0]["field_changes"]["sets"]["to"], 4)
        self.assertEqual(diff["changed"][0]["field_changes"]["rest_s"]["to"], 75)

    def test_build_learning_context_prioritizes_similar_profiles(self):
        rows = [
            {
                "id": 1,
                "student_id": 10,
                "generated_plan_json": {
                    "plan_meta": {"split": "AB"},
                    "items": [
                        {"week": 1, "day": "A", "exercise_name": "Supino", "sets": 3, "reps": "10", "rest_s": 60, "tempo": "2-0-2"}
                    ],
                },
                "plan_json": {
                    "plan_meta": {"split": "ABC"},
                    "items": [
                        {"week": 1, "day": "A", "exercise_name": "Supino", "sets": 4, "reps": "10", "rest_s": 75, "tempo": "2-0-2"},
                        {"week": 1, "day": "A", "exercise_name": "Crucifixo", "sets": 3, "reps": "12", "rest_s": 45, "tempo": "2-1-2"},
                    ],
                },
                "edit_count": 1,
                "objectives": ["hipertrofia"],
                "level": "intermediario",
                "restrictions": ["joelho"],
                "injuries": [],
                "freq_per_week": 4,
                "session_time_min": 50,
            },
            {
                "id": 2,
                "student_id": 11,
                "generated_plan_json": {
                    "plan_meta": {"split": "full body"},
                    "items": [
                        {"week": 1, "day": "A", "exercise_name": "Remada", "sets": 3, "reps": "12", "rest_s": 60, "tempo": "2-0-2"}
                    ],
                },
                "plan_json": {
                    "plan_meta": {"split": "full body"},
                    "items": [
                        {"week": 1, "day": "A", "exercise_name": "Remada", "sets": 3, "reps": "12", "rest_s": 60, "tempo": "2-0-2"}
                    ],
                },
                "edit_count": 0,
                "objectives": ["emagrecimento"],
                "level": "iniciante",
                "restrictions": [],
                "injuries": [],
                "freq_per_week": 2,
                "session_time_min": 30,
            },
        ]
        db = FakeSession({"FROM plan_llm_comparisons plc": rows})
        target_bundle = {
            "assessment": {
                "objectives": ["hipertrofia"],
                "level": "intermediario",
                "restrictions": ["joelho"],
                "injuries": [],
                "freq_per_week": 4,
                "session_time_min": 55,
            }
        }

        context = build_llm_learning_context(db, target_bundle=target_bundle)

        self.assertEqual(context["summary"]["plans_analyzed"], 1)
        self.assertGreater(context["profile_focus"]["avg_profile_similarity"], 0.5)
        self.assertEqual(context["summary"]["top_added_exercises"][0]["exercise_name"], "crucifixo")
        self.assertEqual(context["quality_metrics"]["plans_used_for_learning"], 1)
        self.assertLess(context["quality_metrics"]["historical_alignment_score"], 1.0)

    def test_analyze_plan_differences_returns_edit_ratio(self):
        plan_rows = [
            {
                "generated_plan_json": {
                    "plan_meta": {"split": "AB"},
                    "items": [
                        {"week": 1, "day": "A", "exercise_name": "Supino", "sets": 3, "reps": "10", "rest_s": 60, "tempo": "2-0-2"}
                    ],
                },
                "plan_json": {
                    "plan_meta": {"split": "ABC"},
                    "items": [
                        {"week": 1, "day": "A", "exercise_name": "Supino", "sets": 4, "reps": "10", "rest_s": 60, "tempo": "2-0-2"}
                    ],
                },
                "edit_count": 1,
            }
        ]
        version_rows = [
            {"version_number": 1, "source": "llm", "plan_json": {}, "created_at": "2026-03-01"},
            {"version_number": 2, "source": "teacher", "plan_json": {}, "created_at": "2026-03-02"},
        ]
        db = FakeSession(
            {
                "FROM plans WHERE id = :pid": plan_rows,
                "FROM plan_versions WHERE plan_id = :pid": version_rows,
            }
        )

        analysis = analyze_plan_differences(db, 99)

        self.assertTrue(analysis["split_changed"])
        self.assertEqual(analysis["edit_ratio"], 1.0)
        self.assertEqual(len(analysis["sets_reps_load_rest_changes"]), 1)

    def test_sanitize_bundle_for_prompt_removes_direct_identifiers(self):
        bundle = {
            "student": {"id": 1, "name": "Lucas", "sex": "M", "age": 30},
            "assessment": {
                "history": "Telefone 11999999999 e email pessoa@teste.com",
                "case_notes": "Aluno prefere treino cedo",
                "objectives": ["hipertrofia"],
                "posture": None,
                "injuries": [],
                "restrictions": [],
                "level": "intermediario",
                "freq_per_week": 4,
                "session_time_min": 50,
                "equipment": ["halter"],
                "red_flags": [],
                "readiness": {},
                "periodization": {},
                "status": "active",
            },
            "measurement": {
                "height_m": 1.8,
                "weight_kg": 82,
                "body_fat_percent": 15,
                "muscle_mass_kg": 37,
                "bmi": 25.3,
                "source": "bioimpedancia",
                "notes": "nao deveria ir para o prompt",
            },
        }

        sanitized = sanitize_bundle_for_prompt(bundle)

        self.assertNotIn("id", sanitized["student"])
        self.assertNotIn("name", sanitized["student"])
        self.assertNotIn("notes", sanitized["measurement"])
        self.assertIn("[redacted-number]", sanitized["assessment"]["history"])
        self.assertIn("[redacted-email]", sanitized["assessment"]["history"])

    def test_build_plan_comparison_snapshot_contains_similarity_and_summary(self):
        original_plan = {
            "plan_meta": {"split": "AB"},
            "items": [
                {"week": 1, "day": "A", "exercise_name": "Supino", "sets": 3, "reps": "10", "rest_s": 60, "tempo": "2-0-2"}
            ],
        }
        final_plan = {
            "plan_meta": {"split": "ABC"},
            "items": [
                {"week": 1, "day": "A", "exercise_name": "Supino", "sets": 4, "reps": "10", "rest_s": 75, "tempo": "2-0-2"},
                {"week": 1, "day": "A", "exercise_name": "Crucifixo", "sets": 3, "reps": "12", "rest_s": 45, "tempo": "2-1-2"},
            ],
        }

        snapshot = build_plan_comparison_snapshot(7, original_plan, final_plan)

        self.assertEqual(snapshot["plan_id"], 7)
        self.assertLess(snapshot["similarity_score"], 1.0)
        self.assertEqual(snapshot["comparison_json"]["summary"]["additions_count"], 1)
        self.assertTrue(snapshot["comparison_json"]["summary"]["split_changed"])

    def test_calculate_plan_similarity_returns_full_match_for_identical_plans(self):
        plan = {
            "plan_meta": {"split": "AB"},
            "items": [
                {"week": 1, "day": "A", "exercise_name": "Supino", "sets": 3, "reps": "10", "rest_s": 60, "tempo": "2-0-2"}
            ],
        }

        similarity = calculate_plan_similarity(plan, plan)

        self.assertEqual(similarity, 1.0)

    def test_build_student_plan_mcp_context_returns_compact_payload(self):
        current_plan_rows = [
            {
                "id": 7,
                "assessment_id": 12,
                "measurement_id": 18,
                "plan_json": {"plan_meta": {"split": "ABC"}, "items": []},
                "generated_plan_json": {"plan_meta": {"split": "AB"}, "items": []},
                "edit_count": 2,
                "updated_at": "2026-03-12T10:00:00",
            }
        ]
        comparison_rows = [
            {
                "id": 1,
                "plan_id": 7,
                "llm_plan_json": {"plan_meta": {"split": "AB"}, "items": []},
                "edited_plan_json": {"plan_meta": {"split": "ABC"}, "items": []},
                "similarity_score": 0.82,
                "comparison_json": {"summary": {"split_changed": True}},
                "created_at": "2026-03-11T10:00:00",
                "updated_at": "2026-03-12T10:00:00",
            }
        ]
        learning_rows = [
            {
                "id": 7,
                "student_id": 20,
                "generated_plan_json": {
                    "plan_meta": {"split": "AB"},
                    "items": [
                        {"week": 1, "day": "A", "exercise_name": "Supino", "sets": 3, "reps": "10", "rest_s": 60, "tempo": "2-0-2"}
                    ],
                },
                "plan_json": {
                    "plan_meta": {"split": "ABC"},
                    "items": [
                        {"week": 1, "day": "A", "exercise_name": "Supino", "sets": 4, "reps": "10", "rest_s": 75, "tempo": "2-0-2"}
                    ],
                },
                "edit_count": 2,
                "objectives": ["hipertrofia"],
                "level": "intermediario",
                "restrictions": [],
                "injuries": [],
                "freq_per_week": 4,
                "session_time_min": 50,
                "similarity_score": 0.82,
                "comparison_json": {"summary": {"split_changed": True}},
            }
        ]
        db = FakeSession(
            {
                "FROM student_current_plans scp": current_plan_rows,
                "FROM plan_llm_comparisons": comparison_rows,
                "FROM plan_llm_comparisons plc": learning_rows,
            }
        )

        context = build_student_plan_mcp_context(db, 20)

        self.assertEqual(context["student_id"], 20)
        self.assertEqual(context["current_plan"]["plan_id"], 7)
        self.assertEqual(context["current_plan_comparison"]["similarity_score"], 0.82)
        self.assertEqual(context["learning_diagnostics"]["summary"]["plans_analyzed"], 1)


if __name__ == "__main__":
    unittest.main()
