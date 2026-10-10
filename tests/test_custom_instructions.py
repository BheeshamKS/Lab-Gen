"""
Unit tests for Custom Instructions & Requirements in LabGenius.
Tests both online prompt injection and deterministic offline heuristics.
"""

import unittest
from labgenius.config import Config
from labgenius.solver import TaskSolver
from labgenius.parser import LabTask


class TestCustomInstructions(unittest.TestCase):

    def setUp(self):
        self.cfg = Config.load()
        self.solver = TaskSolver(self.cfg)

    def test_custom_instructions_inline_comments(self):
        """Verifies custom instructions requesting comments add comments and are not stripped."""
        task = LabTask(task_id=1, title="List Processing", description="Write function to calculate stats", language="python")
        sol = self.solver.solve_task(task, custom_instructions="Add detailed inline comments explaining the logic")
        
        # Must contain comment symbols
        self.assertIn("#", sol.code)
        self.assertIn("Operation:", sol.code)

    def test_custom_instructions_language_override(self):
        """Verifies custom instructions requesting a language override change the language."""
        task = LabTask(task_id=2, title="Data Processing", description="Calculate averages", language="python")
        sol = self.solver.solve_task(task, custom_instructions="Solve this in C++ instead of Python")
        
        self.assertEqual(sol.language, "cpp")
        self.assertTrue(sol.file_name.endswith(".cpp"))
        self.assertIn("#include <iostream>", sol.code)

    def test_custom_instructions_concise_explanation(self):
        """Verifies custom instructions requesting concise explanations condense output."""
        task = LabTask(task_id=3, title="Array Search", description="Find elements", language="python")
        sol = self.solver.solve_task(task, custom_instructions="Keep explanation concise under 2 sentences")
        
        sentences = [s.strip() for s in sol.explanation.split(".") if s.strip()]
        self.assertLessEqual(len(sentences), 2)

    def test_system_prompt_carries_custom_instructions(self):
        """Verifies the LLM system prompt carries the user override instructions with highest priority."""
        task = LabTask(task_id=4, title="Database Task", description="Create table", language="sql")
        prompt = self.solver._build_system_prompt(task, custom_instructions="Do not use VARCHAR, use NVARCHAR exclusively")
        
        self.assertIn("SPECIAL USER INSTRUCTIONS FOR SOLVING THIS LAB", prompt)
        self.assertIn("Do not use VARCHAR, use NVARCHAR exclusively", prompt)


if __name__ == "__main__":
    unittest.main()
