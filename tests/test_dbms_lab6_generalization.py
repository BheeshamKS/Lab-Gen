"""
Comprehensive Generalization & Future-Proofing Tests for DBMS Lab 6 & Dynamic Synthesizer.
Verifies that:
1. All 15 tasks of DBMS Lab 6 generate distinct, non-repetitive, valid queries matching requirements.
2. All 15 queries execute cleanly against SQLite with actual populated rows (no dummy stubs or column errors).
3. Arbitrary unseen database schemas (e.g., Inventory / Orders) are extracted and synthesized forward-looking.
4. SQL runner auto-heals stale / mismatched schemas without crashing.
5. Dynamic DSA synthesizer produces task-tailored algorithms rather than generic stubs.
"""

import sqlite3
import unittest
import tempfile
from pathlib import Path

from labgenius.config import Config
from labgenius.parser import ManualParser, LabTask
from labgenius.solver import TaskSolver
from labgenius.runner import CodeRunner
from labgenius.sql_runner import execute_sql_file
from labgenius.synthesizer import DynamicSQLSynthesizer, DynamicDSASynthesizer

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestDBMSLab6Generalization(unittest.TestCase):

    def setUp(self):
        self.cfg = Config.load()
        self.solver = TaskSolver(self.cfg)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        self.cfg.system.workspace_dir = str(self.workspace)
        self.runner = CodeRunner(self.cfg)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_01_dbms_lab6_15_unique_queries(self):
        """Verifies that all 15 tasks of DBMS Lab 6 produce unique, requirement-aligned queries."""
        pdf_path = REPO_ROOT / "workspace" / "8fd014e9648a" / "DBMS - Lab 06-edit.pdf"
        self.assertTrue(pdf_path.exists(), f"Lab 6 manual missing: {pdf_path}")

        parser = ManualParser(pdf_path)
        manual = parser.parse()
        self.assertEqual(len(manual.tasks), 15)

        solutions = [self.solver.solve_task(t, lab_context=manual.context) for t in manual.tasks]
        query_codes = [s.code.strip() for s in solutions]

        # Ensure no two tasks have identical SQL code
        unique_codes = set(query_codes)
        self.assertEqual(
            len(unique_codes),
            15,
            f"Expected 15 unique queries, but found only {len(unique_codes)} unique queries!"
        )

        # Ensure none of the queries contain the old broken fallback stub
        for idx, code in enumerate(query_codes, 1):
            self.assertNotIn("WHERE ID >= 1 ORDER BY ID ASC", code, f"Task {idx} contains legacy fallback stub!")
            self.assertIn("Hospital", code, f"Task {idx} did not target the Hospital table!")

        # Verify specific query logic
        self.assertIn("Department = 'Cardiology'", query_codes[0])
        self.assertIn("Age > 50", query_codes[1])
        self.assertIn("SELECT DISTINCT BloodGroup", query_codes[2])
        self.assertIn("DISTINCT", query_codes[3])
        self.assertIn("AND", query_codes[4])
        self.assertIn("OR", query_codes[5])
        self.assertIn("BETWEEN", query_codes[7])
        self.assertIn("BETWEEN", query_codes[13])
        self.assertIn("Karachi", query_codes[12])
        self.assertIn("Lahore", query_codes[12])
        self.assertIn("Emergency", query_codes[12])

    def test_02_dbms_lab6_clean_execution_and_rows(self):
        """Verifies that all 15 queries execute cleanly, returning formatted data rows without errors."""
        pdf_path = REPO_ROOT / "workspace" / "8fd014e9648a" / "DBMS - Lab 06-edit.pdf"
        parser = ManualParser(pdf_path)
        manual = parser.parse()

        db_path = self.workspace / "dbms_lab.db"
        DynamicSQLSynthesizer.prepare_database(db_path, manual.context, tasks=manual.tasks)

        for task in manual.tasks:
            sol = self.solver.solve_task(task, lab_context=manual.context)
            sql_file = self.workspace / f"query_{task.task_id:02d}.sql"
            sql_file.write_text(sol.code, encoding="utf-8")

            output = execute_sql_file(sql_file, db_path, "Test Student", "25F-DS-020")
            self.assertNotIn("Invalid object name", output, f"Task {task.task_id} failed: {output}")
            self.assertNotIn("no such column", output, f"Task {task.task_id} column missing: {output}")
            self.assertIn("affected", output, f"Task {task.task_id} produced no affected row count: {output}")

    def test_03_arbitrary_unseen_database_generalization(self):
        """Verifies dynamic schema extraction and synthesis on an unseen ECommerce database."""
        context = "Warehouse Table Fields: ItemSKU, ItemName, Category, StockLevel, ReorderPoint, UnitCost, SupplierCity"
        task1 = LabTask(
            task_id=1,
            title="Low Stock Items",
            description="Retrieve all items from Warehouse where StockLevel is below 20 and Category is 'Electronics'.",
            language="sql"
        )
        task2 = LabTask(
            task_id=2,
            title="Unique Supplier Cities",
            description="Display all unique supplier cities recorded in the warehouse.",
            language="sql"
        )
        task3 = LabTask(
            task_id=3,
            title="Moderate Cost Inventory",
            description="Retrieve all items where UnitCost is between 1500 and 5000.",
            language="sql"
        )

        schema = DynamicSQLSynthesizer.extract_schema(context, tasks=[task1, task2, task3])
        self.assertEqual(schema.table_name, "Warehouse")
        self.assertIn("StockLevel", schema.columns)
        self.assertIn("ItemSKU", schema.columns)

        db_path = self.workspace / "warehouse.db"
        DynamicSQLSynthesizer.prepare_database(db_path, context, tasks=[task1, task2, task3])

        code1, exp1 = DynamicSQLSynthesizer.synthesize_task_solution(task1, schema=schema, lab_context=context)
        self.assertIn("Warehouse", code1)
        self.assertIn("StockLevel", code1)

        code2, exp2 = DynamicSQLSynthesizer.synthesize_task_solution(task2, schema=schema, lab_context=context)
        self.assertIn("DISTINCT", code2)
        self.assertIn("SupplierCity", code2)

        code3, exp3 = DynamicSQLSynthesizer.synthesize_task_solution(task3, schema=schema, lab_context=context)
        self.assertIn("BETWEEN 1500 AND 5000", code3)

    def test_04_sql_runner_stale_schema_auto_healing(self):
        """Verifies sql_runner automatically detects missing columns and repairs the database schema."""
        db_path = self.workspace / "stale_test.db"
        conn = sqlite3.connect(str(db_path))
        # Intentionally create an obsolete schema missing Department and Age
        conn.execute("CREATE TABLE Hospital (ID INT PRIMARY KEY, Name VARCHAR(50));")
        conn.execute("INSERT INTO Hospital VALUES (1, 'Old Record');")
        conn.commit()
        conn.close()

        # Place session.json with full schema definition in the directory
        import json
        session_data = {
            "manual": {
                "context": "Hospital Table Fields: PatientID, PatientName, Age, Gender, Department, City, BloodGroup, BillAmount",
                "tasks": [
                    {"task_id": 1, "title": "Cardiology Patients", "description": "Retrieve patients in Cardiology."}
                ]
            }
        }
        (self.workspace / "session.json").write_text(json.dumps(session_data), encoding="utf-8")

        query_file = self.workspace / "test_heal.sql"
        query_file.write_text("SELECT * FROM Hospital WHERE Department = 'Cardiology';", encoding="utf-8")

        output = execute_sql_file(query_file, db_path, "Test Student", "001")
        self.assertNotIn("no such column", output)
        self.assertIn("Ali Khan", output)
        self.assertIn("Cardiology", output)

    def test_05_dynamic_dsa_synthesizer_algorithms(self):
        """Verifies forward-looking algorithmic synthesis for unseen DSA tasks."""
        task_kruskal = LabTask(
            task_id=10,
            title="Minimum Spanning Tree",
            description="Implement Kruskal's algorithm to find the minimum spanning tree of a weighted graph.",
            language="python"
        )
        task_edit_dist = LabTask(
            task_id=11,
            title="Levenshtein Edit Distance",
            description="Compute the minimum edit distance between two strings using dynamic programming.",
            language="python"
        )

        code_k, exp_k, lang_k = DynamicDSASynthesizer.synthesize_task_solution(task_kruskal)
        self.assertIn("find", code_k.lower())
        self.assertIn("union", code_k.lower())
        self.assertNotIn("process_data_stream", code_k)

        code_e, exp_e, lang_e = DynamicDSASynthesizer.synthesize_task_solution(task_edit_dist)
        self.assertIn("dp", code_e.lower())
        self.assertNotIn("process_data_stream", code_e)


if __name__ == "__main__":
    unittest.main()
