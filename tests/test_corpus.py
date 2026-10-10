"""
Unit tests for Persistent Reference Corpus.
"""

import unittest
from pathlib import Path
from labgenius.corpus import ReferenceCorpus, ReferenceTask


class TestReferenceCorpus(unittest.TestCase):

    def setUp(self):
        self.corpus = ReferenceCorpus()

    def test_corpus_initialization(self):
        """Verifies corpus contains verified entries across both DSA and DBMS."""
        self.assertGreaterEqual(len(self.corpus.entries), 10)
        subjects = {e.subject for e in self.corpus.entries}
        self.assertIn("dsa", subjects)
        self.assertIn("dbms", subjects)

    def test_all_entries_verified(self):
        """Verifies all reference tasks in the canonical corpus are verified."""
        for e in self.corpus.entries:
            self.assertTrue(e.verified, f"Entry {e.lab_id} Task {e.task_id} not marked verified")
            self.assertTrue(len(e.code_pattern) > 20, f"Entry {e.lab_id} has insufficient code pattern")

    def test_search_dsa_references(self):
        """Verifies searching relevant references for DSA topics."""
        refs = self.corpus.find_relevant_references("dsa", "Stack & Queue", "implement lifo push pop")
        self.assertTrue(any("Stack" in r.topic or "Queue" in r.topic for r in refs))

    def test_search_dbms_references(self):
        """Verifies searching relevant references for DBMS constraints and DDL."""
        refs = self.corpus.find_relevant_references("dbms", "Table Constraints", "create table with primary key unique check")
        self.assertTrue(any("Constraints" in r.topic or "Table" in r.topic for r in refs))

    def test_held_out_exclusion(self):
        """Verifies that held-out lab ID is strictly excluded during leave-one-out testing."""
        held_out_lab = "DBMS_LAB04"
        refs = self.corpus.find_relevant_references(
            subject="dbms",
            task_title="SQL Integrity Constraints",
            task_desc="employee primary key check unique",
            exclude_lab_id=held_out_lab
        )
        for r in refs:
            self.assertNotEqual(r.lab_id, held_out_lab, "Held-out lab leaked into reference results!")

    def test_guidance_formatting(self):
        """Verifies architectural prompt formatting contains no answers to copy."""
        refs = self.corpus.find_relevant_references("dsa", "Linked List", "insert at head and tail")
        guidance = self.corpus.format_guidance_for_prompt(refs)
        self.assertIn("ARCHITECTURAL & SOLUTION CONVENTIONS", guidance)
        self.assertIn("DO NOT copy the specific identifiers", guidance)


if __name__ == "__main__":
    unittest.main()
