import unittest

from src.IA.llm_generator import LLMGenerator
from src.services.llm_service import build_generation_payload


class LLMMCPIntegrationTests(unittest.TestCase):
    def test_generator_prompt_includes_privacy_and_safety_rules(self):
        generator = LLMGenerator.__new__(LLMGenerator)
        payload = {
            "generation_context": {
                "student": {"sex": "M", "age": 30},
                "assessment": {
                    "objectives": ["hipertrofia"],
                    "restrictions": ["joelho"],
                    "injuries": ["ombro"],
                    "red_flags": ["dor aguda"],
                    "readiness": {"fatigue": "alta"},
                },
                "measurement": {"weight_kg": 80},
                "_learning_context": {"summary": {"plans_analyzed": 1}},
            },
            "current_plan_context": {
                "current_plan": {"plan_id": 7},
            },
        }

        prompt = generator._build_prompt(payload)

        self.assertIn("Nunca reproduza ou solicite dados sensiveis", prompt)
        self.assertIn("Restricoes, lesoes, red_flags, readiness, warnings", prompt)
        self.assertIn("alertas_de_seguranca", prompt)
        self.assertIn("plano_atual_e_memoria", prompt)

    def test_build_generation_payload_preserves_expected_shape(self):
        class FakeDB:
            pass

        payload = build_generation_payload.__globals__["build_generation_context"]
        current_plan = build_generation_payload.__globals__["build_student_plan_mcp_context"]

        build_generation_payload.__globals__["build_generation_context"] = lambda **kwargs: {
            "student": {"sex": "F", "age": 28},
            "assessment": {"red_flags": [], "restrictions": [], "injuries": []},
            "measurement": {},
        }
        build_generation_payload.__globals__["build_student_plan_mcp_context"] = lambda db, student_id: {
            "student_id": student_id
        }
        try:
            result = build_generation_payload(
                db=FakeDB(),
                student_id=1,
                assessment_id=2,
                measurement_id=3,
                include_learning=True,
                include_current_plan=True,
            )
        finally:
            build_generation_payload.__globals__["build_generation_context"] = payload
            build_generation_payload.__globals__["build_student_plan_mcp_context"] = current_plan

        self.assertEqual(result["student_id"], 1)
        self.assertEqual(result["assessment_id"], 2)
        self.assertEqual(result["measurement_id"], 3)
        self.assertIn("generation_context", result)
        self.assertEqual(result["current_plan_context"]["student_id"], 1)


if __name__ == "__main__":
    unittest.main()
