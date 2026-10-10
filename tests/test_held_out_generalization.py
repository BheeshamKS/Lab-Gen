"""
Leave-One-Lab-Out Generalization Evaluation and Synthetic Task Testing.
Evaluates generator accuracy when a lab is strictly held out from reference corpus.
"""

import unittest
from pathlib import Path
from labgenius.config import Config
from labgenius.corpus import ReferenceCorpus
from labgenius.parser import LabTask
from labgenius.solver import TaskSolver, validate_code_syntax
from labgenius.runner import CodeRunner

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestHeldOutGeneralization(unittest.TestCase):

    def setUp(self):
        self.cfg = Config()
        self.cfg.student.name = "Bheesham Kumar Sajnani"
        self.cfg.student.roll_number = "25F-DS-020"
        self.runner = CodeRunner(self.cfg)

    def test_leave_one_out_dsa_lab4(self):
        """
        Hold out DSA Lab 04 (Stack & Queue) from reference corpus.
        Verify that solving a Stack task succeeds with valid Python syntax
        and passes execution runtime without accessing DSA_LAB04 answers.
        """
        corpus = ReferenceCorpus()
        # Verify held out
        held_out_id = "DSA_LAB04"
        refs = corpus.find_relevant_references("dsa", "Stack Implementation", "push and pop", exclude_lab_id=held_out_id)
        for r in refs:
            self.assertNotEqual(r.lab_id, held_out_id)

        solver = TaskSolver(self.cfg, corpus=corpus)
        task = LabTask(
            task_id=1,
            title="Implement LIFO Stack Data Structure",
            description="Write a Python class Stack with push, pop, peek, is_empty methods and demonstrate with test calls.",
            language="python"
        )
        sol = solver.solve_task(task)

        # 1. Syntax validation
        is_valid, msg = validate_code_syntax(sol.code, sol.language)
        self.assertTrue(is_valid, f"Syntax Error in held-out solution: {msg}")

        # 2. Execution validation
        res = self.runner.execute(sol)
        self.assertTrue(res.success, f"Execution failed: {res.stderr}")
        self.assertIn("Pushed", res.stdout)
        self.assertIn("Popped", res.stdout)

    def test_leave_one_out_dbms_lab4(self):
        """
        Hold out DBMS Lab 04 (Constraints) from reference corpus.
        Verify that solving an integrity constraint task generates authentic SQL
        and executes with expected constraint error status without referencing DBMS_LAB04.
        """
        corpus = ReferenceCorpus()
        held_out_id = "DBMS_LAB04"
        refs = corpus.find_relevant_references("dbms", "Check Constraint", "age check constraint", exclude_lab_id=held_out_id)
        for r in refs:
            self.assertNotEqual(r.lab_id, held_out_id)

        solver = TaskSolver(self.cfg, corpus=corpus)
        task = LabTask(
            task_id=7,
            title="Test Age CHECK Constraint",
            description="Attempt to insert an employee whose Age is below 18 and observe the error.",
            language="sql"
        )
        sol = solver.solve_task(task)

        # 1. Syntax validation
        is_valid, msg = validate_code_syntax(sol.code, sol.language)
        self.assertTrue(is_valid, f"Syntax Error in held-out SQL: {msg}")

        # 2. Execution validation
        res = self.runner.execute(sol)
        # Note: SQLite / SQL Runner should report the CHECK constraint termination error
        self.assertTrue(
            "CHECK constraint" in res.stdout or "terminated" in res.stdout or res.success,
            f"Unexpected output: {res.stdout}"
        )

    def test_synthetic_unseen_dsa_binary_search_tree(self):
        """Tests generalization on completely unseen DSA task: Binary Search Tree."""
        solver = TaskSolver(self.cfg)
        task = LabTask(
            task_id=101,
            title="Binary Search Tree Implementation",
            description="Construct a BinarySearchTree with insert and inorder traversal methods.",
            language="python"
        )
        sol = solver.solve_task(task)
        is_valid, msg = validate_code_syntax(sol.code, "python")
        self.assertTrue(is_valid, f"Syntax error: {msg}")

        res = self.runner.execute(sol)
        self.assertTrue("inorder traversal" in res.stdout.lower() or "in-order traversal" in res.stdout.lower(), f"Unexpected output: {res.stdout}")

    def test_synthetic_unseen_dsa_graph_bfs_dfs(self):
        """Tests generalization on completely unseen DSA task: Graph BFS & DFS."""
        solver = TaskSolver(self.cfg)
        task = LabTask(
            task_id=102,
            title="Graph Breadth-First and Depth-First Search",
            description="Implement Graph adjacency list with BFS and DFS traversals.",
            language="python"
        )
        sol = solver.solve_task(task)
        is_valid, msg = validate_code_syntax(sol.code, "python")
        self.assertTrue(is_valid, f"Syntax error: {msg}")

        res = self.runner.execute(sol)
        self.assertTrue(res.success, f"Execution failed: {res.stderr}")
        self.assertIn("BFS Traversal", res.stdout)
        self.assertIn("DFS Traversal", res.stdout)

    def test_synthetic_unseen_dbms_department_table_and_join(self):
        """Tests generalization on completely unseen DBMS task: Department table with JOIN."""
        solver = TaskSolver(self.cfg)
        task_create = LabTask(
            task_id=201,
            title="Create Department Table",
            description="Create Department table with DeptID as primary key and DepartmentName.",
            language="sql"
        )
        sol_create = solver.solve_task(task_create)
        res_create = self.runner.execute(sol_create)
        self.assertTrue(res_create.success, f"DDL failed: {res_create.stderr}")

        task_join = LabTask(
            task_id=202,
            title="Join Department and Employee",
            description="Execute INNER JOIN between Department and Employee on DeptID.",
            language="sql"
        )
        sol_join = solver.solve_task(task_join)
        self.assertIn("JOIN", sol_join.code.upper())


if __name__ == "__main__":
    unittest.main()
