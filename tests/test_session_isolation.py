"""
Unit and Integration Tests for Session Isolation in LabGenius.
Verifies multi-session coexistence, SQLite index persistence, and independent workspaces.
"""

import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from labgenius.state import SessionManager, StudentInfo, ManualInfo, Requirement, RequirementType, RequirementStatus
from web_app import app, session_manager

REPO_ROOT = Path(__file__).resolve().parent.parent


class TestSessionIsolation(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_01_session_manager_crud_and_sqlite(self):
        """Verifies SessionManager properly persists and retrieves sessions from SQLite and disk."""
        sm = SessionManager(workspace_root=REPO_ROOT / "workspace" / "test_workspace")
        sess = sm.create_session(
            student_info=StudentInfo(name="Alice Test", roll_number="25F-DS-100"),
            manual_info=ManualInfo(title="Operating Systems Lab 1", course_name="Operating Systems"),
        )
        self.assertIsNotNone(sess.session_id)
        
        # Add requirement
        req = Requirement(
            id="task_1",
            task_id=1,
            type=RequirementType.TASK,
            title="Process Forking",
            status=RequirementStatus.VALIDATED,
            code="int main() { fork(); return 0; }",
        )
        sess.requirements.append(req)
        sm.save_session(sess)

        # Retrieve and verify
        loaded = sm.get_session(sess.session_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.student.name, "Alice Test")
        self.assertEqual(loaded.manual.title, "Operating Systems Lab 1")
        self.assertEqual(len(loaded.requirements), 1)
        self.assertEqual(loaded.requirements[0].title, "Process Forking")

        # Verify listing
        sessions_list = sm.list_sessions()
        ids = [s["session_id"] for s in sessions_list]
        self.assertIn(sess.session_id, ids)

        # Delete session
        deleted = sm.delete_session(sess.session_id)
        self.assertTrue(deleted)
        self.assertIsNone(sm.get_session(sess.session_id))

    def test_02_concurrent_multi_session_isolation(self):
        """
        Generates two different labs concurrently with explicit session_ids:
        - Session 1: DBMS Lab 01
        - Session 2: DSA Lab 02
        Asserts that both sessions remain isolated and do not contaminate each other.
        """
        # 1. Run Session 1 (DBMS Lab 01)
        dbms_path = REPO_ROOT / "uploads" / "DBMS Lab 01.docx"
        with open(dbms_path, "rb") as f:
            res1 = self.client.post(
                "/api/generate-lab",
                data={
                    "name": "Student A",
                    "roll_number": "25F-DS-001",
                    "subject": "auto",
                    "formats": "docx",
                    "provider": "offline",
                    "session_id": "test_sess_dbms_01",
                },
                files={"manual_file": ("DBMS Lab 01.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            )
        data1 = res1.json()
        self.assertTrue(data1.get("success"), f"Session 1 failed: {data1.get('error')}")
        self.assertEqual(data1.get("session_id"), "test_sess_dbms_01")
        self.assertEqual(data1.get("course_name"), "Database Management Systems (DBMS)")

        # 2. Run Session 2 (DSA Lab 02)
        dsa_path = REPO_ROOT / "uploads" / "Data Structure Laboratory Manual L2.docx"
        with open(dsa_path, "rb") as f:
            res2 = self.client.post(
                "/api/generate-lab",
                data={
                    "name": "Student B",
                    "roll_number": "25F-DS-002",
                    "subject": "auto",
                    "formats": "docx",
                    "provider": "offline",
                    "session_id": "test_sess_dsa_02",
                },
                files={"manual_file": ("Data Structure Laboratory Manual L2.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            )
        data2 = res2.json()
        self.assertTrue(data2.get("success"), f"Session 2 failed: {data2.get('error')}")
        self.assertEqual(data2.get("session_id"), "test_sess_dsa_02")
        self.assertEqual(data2.get("course_name"), "Data Structures and Algorithms")

        # 3. Query Session 1 and Session 2 individually via API
        curr_dbms = self.client.get("/api/current-lab?session_id=test_sess_dbms_01").json()
        curr_dsa = self.client.get("/api/current-lab?session_id=test_sess_dsa_02").json()

        self.assertTrue(curr_dbms.get("success"))
        self.assertEqual(curr_dbms.get("course_name"), "Database Management Systems (DBMS)")

        self.assertTrue(curr_dsa.get("success"))
        self.assertEqual(curr_dsa.get("course_name"), "Data Structures and Algorithms")

        # 4. Check workspace directories are distinct and isolated
        dbms_dir = REPO_ROOT / "workspace" / "test_sess_dbms_01"
        dsa_dir = REPO_ROOT / "workspace" / "test_sess_dsa_02"
        self.assertTrue(dbms_dir.exists())
        self.assertTrue(dsa_dir.exists())

        # 5. Clean up test sessions
        self.client.post("/api/close-lab", data={"session_id": "test_sess_dbms_01"})
        self.client.post("/api/close-lab", data={"session_id": "test_sess_dsa_02"})
        self.assertFalse(dbms_dir.exists())
        self.assertFalse(dsa_dir.exists())


if __name__ == "__main__":
    unittest.main()
