"""Validate observation semantics using temporary data, without model calls."""
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from observe_late_risk import observe


class ObservationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.database = self.root / "db.sqlite3"
        with sqlite3.connect(self.database) as db:
            db.executescript('''
                CREATE TABLE shared_models_customer (id INTEGER, name TEXT);
                CREATE TABLE shared_models_book (id INTEGER, title TEXT, category TEXT);
                CREATE TABLE shared_models_loan (id INTEGER, Customer_id INTEGER,
                    loan_date TEXT, due_date TEXT, return_date TEXT);
                CREATE TABLE shared_models_bookloan (id INTEGER, Loan_id INTEGER,
                    Book_id INTEGER, late_risk TEXT);
                INSERT INTO shared_models_customer VALUES (1, 'bob');
                INSERT INTO shared_models_book VALUES (1, 'Demo History Book', 'HISTORY');
                INSERT INTO shared_models_loan VALUES (1, 1, '2026-09-14', '2026-09-28', '');
                INSERT INTO shared_models_bookloan VALUES (1, 1, 1, 'LOW');
            ''')
        self.creation = {"model": "BookLoan", "pk": 1, "created": True,
                         "invocation_id": "creation-1", "status": "success",
                         "write_back": {"requested": True, "intended_value": "HIGH"},
                         "prompts": [{"template": "risk", "prompt": "test prompt"}]}

    def write_trace(self, records):
        (self.root / "ai_invocations.jsonl").write_text(
            "\n".join(json.dumps(record) for record in records) + "\n")

    def test_current_db_is_independent_of_intent_and_later_save(self):
        self.write_trace([self.creation, {"model": "BookLoan", "pk": 1,
                         "created": False, "invocation_id": "save-2",
                         "status": "skipped", "skip_reason": "not_created"}])
        before = self.database.read_bytes()
        result = observe(self.root, 1)
        self.assertEqual(result["assessment"]["invocation_id"], "creation-1")
        self.assertEqual(result["db_now"]["late_risk"], "LOW")
        self.assertFalse(result["db_matches_intended_now"])
        self.assertEqual(len(result["events_for_this_bookloan"]), 2)
        self.assertNotIn("prompt", result["assessment"]["prompts"][0])
        self.assertEqual(observe(self.root, 1, include_prompt=True)["assessment"]["prompts"][0]["prompt"], "test prompt")
        self.assertEqual(before, self.database.read_bytes())

    def test_missing_or_other_rows_trace_is_not_claimed_as_assessment(self):
        self.write_trace([{**self.creation, "pk": 99}])
        self.assertIsNone(observe(self.root, 1)["assessment"])
        with self.assertRaises(ValueError):
            observe(self.root, 1, "creation-1")
        with self.assertRaises(ValueError):
            observe(self.root, 99)

    def test_per_book_schema_uses_each_books_own_return(self):
        with sqlite3.connect(self.database) as db:
            db.execute('ALTER TABLE shared_models_bookloan ADD COLUMN return_date TEXT')
            db.execute("UPDATE shared_models_bookloan SET return_date='2026-09-15'")
            db.execute("UPDATE shared_models_loan SET return_date='2026-10-10'")
        observed=observe(self.root,1)
        self.assertEqual(observed['return_unit'],'book_loan')
        self.assertEqual(observed['db_now']['return_date'],'2026-09-15')

    def test_ambiguous_or_partial_trace_requires_explicit_resolution(self):
        self.write_trace([self.creation, {**self.creation, "invocation_id": "creation-2"}])
        with self.assertRaises(ValueError):
            observe(self.root, 1)
        self.assertEqual(observe(self.root, 1, "creation-2")["assessment"]["invocation_id"], "creation-2")
        with (self.root / "ai_invocations.jsonl").open("a") as stream:
            stream.write('{"unfinished":')
        with self.assertRaisesRegex(ValueError, "Incomplete/invalid trace"):
            observe(self.root, 1)


if __name__ == "__main__":
    unittest.main()
