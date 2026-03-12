import unittest

from src.mcp.server import mcp
from src.mcp.tools import json_ready


class MCPServerTests(unittest.TestCase):
    def test_registered_tool_names(self):
        tool_names = sorted(tool.name for tool in mcp._tool_manager.list_tools())
        self.assertEqual(
            tool_names,
            [
                "get_current_student_plan",
                "get_generation_context",
                "get_plan_comparison",
                "get_plan_memory",
                "get_professor_learning_diagnostics",
                "get_student_record",
                "get_student_snapshot",
            ],
        )

    def test_json_ready_serializes_nested_values(self):
        payload = {
            "value": 1,
            "items": (1, 2, {"nested": 3}),
        }
        result = json_ready(payload)
        self.assertEqual(result["items"], [1, 2, {"nested": 3}])


if __name__ == "__main__":
    unittest.main()
