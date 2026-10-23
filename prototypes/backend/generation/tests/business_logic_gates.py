"""BL-1.0 contract gates against a freshly generated Django application.

Every test runs inside a rolled-back transaction. HTTP uses Django's full
middleware/URL/template stack; provider transport tests use a local HTTP server.
"""
import argparse
import ast
from contextlib import contextmanager
from copy import deepcopy
from datetime import date, timedelta
import importlib
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import unittest
import uuid
from unittest.mock import patch

parser = argparse.ArgumentParser()
for name in ("prototype", "metadata", "case-data", "output"):
    parser.add_argument("--" + name, required=True)
parser.add_argument("--mode", choices=["fake", "real"], required=True)
ARGS = parser.parse_args()
ROOT = Path(ARGS.prototype)
OUT = Path(ARGS.output)
OUT.mkdir(parents=True, exist_ok=True)
FIXTURE = json.loads(Path(ARGS.case_data).read_text())
METADATA = json.loads(Path(ARGS.metadata).read_text())
GEN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(GEN / "generation_scripts"))
os.environ["DJANGO_SETTINGS_MODULE"] = ROOT.name + ".settings"
os.environ["AI_RUNTIME_FAKE"] = "1"

import django
django.setup()
from django.conf import settings
from django.core.management import call_command
from django.db import transaction, DatabaseError, IntegrityError
from django.test import Client, RequestFactory, override_settings
from django.test.utils import setup_test_environment
from django.urls import path, reverse
from django.utils import timezone
from shared_models.models import Author, Book, Loan, BookLoan, Customer, User
from shared_models import ai_hooks, ai_actions, views as shared_views
from ai_runtime import invoke
from ai_runtime import context, execution, routing
from ai_runtime.configuration import ConfigurationError, validate_ai_config, MODEL_PROFILES
from ai_runtime.reading_plan import run_reading_plan
from utils.ai_generation import validate_metadata
from ai_runtime_assets.configuration import ConfigurationError as GenerationConfigurationError

setup_test_environment()
logging.disable(logging.CRITICAL)  # Expected HTTP refusals are saved as assertions, not noisy server logs.
TODAY = date.fromisoformat(FIXTURE["test_today"])
RISK_KEY = "_AI_CONFIG__BookLoan__late_risk"
PLAN_KEY = "_AI_CONFIG__Customer__reading_plan"
RISK = deepcopy(getattr(ai_hooks, RISK_KEY))
PLAN = deepcopy(getattr(ai_actions, PLAN_KEY))
MEMBER_URL = reverse("member:render_member_customers")
LIBRARY_URL = reverse("librarian:render_librarian_loans")
ACTION = "custom_Customer_generate_reading_plan"
RESULTS = {}
SEED = {"alice_loans": Loan.objects.filter(Customer__name="alice").count(),
        "bob_loans": Loan.objects.filter(Customer__name="bob").count(),
        "history_labels": list(BookLoan.objects.values_list("late_risk", flat=True)),
        "member_email": User.objects.get(username="demo_member").email}


def dump(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str))


def metadata_config(meta, model, field):
    return next(a for d in meta["diagrams"] if d["type"] == "classes" for n in d["nodes"]
                if n.get("cls", {}).get("name") == model for a in n["cls"]["attributes"] if a["name"] == field)


def set_path(config, key, value):
    target = config
    keys = key.split(".")
    for name in keys[:-1]:
        target = target[name]
    target[keys[-1]] = value


class Gates(unittest.TestCase):
    def setUp(self):
        self.gate = self._testMethodName[len("test_"):].replace("_", "-")
        self.folder = OUT / self.gate
        self.folder.mkdir(exist_ok=True)
        self.scope = override_settings(BASE_DIR=self.folder, DEBUG=False)
        self.scope.enable()
        self.clock = patch("django.utils.timezone.localdate", return_value=TODAY)
        self.clock.start()
        self.atomic = transaction.atomic()
        self.atomic.__enter__()
        # Rebuild only this transaction's synthetic fixture, retaining the generated users.
        BookLoan.objects.all().delete()
        Loan.objects.all().delete()
        Book.objects.all().delete()
        Author.objects.all().delete()
        Customer.objects.all().delete()
        self.author = Author.objects.create(name="Demo Author")
        self.books = {b["key"]: Book.objects.create(title=b["title"], category=b["category"], Author=self.author)
                      for b in FIXTURE["books"]}
        self.bob = Customer.objects.create(name="bob", email="bob@example.com")
        self.alice = Customer.objects.create(name="alice", email="alice@example.com")
        self.member = User.objects.get(username="demo_member")
        self.member.email = "bob@example.com"
        self.member.save()
        self.librarian = User.objects.get(username="demo_librarian")
        self.loans = {}
        for row in FIXTURE["bob_completed_loans"]:
            self.loans[row["key"]] = self.loan(**{k: row[k] for k in ("loan_date", "due_date", "return_date")},
                                               book=self.books[row["book"]])
        self.client = Client()
        self.client.force_login(self.member)
        self.staff = Client()
        self.staff.force_login(self.librarian)
        self.http = []
        self.before = self.db()

    def tearDown(self):
        traces = self.traces()
        dump(self.folder / "db.json", {"before": self.before, "after": self.db(),
             "note": "After assertions, this isolated transaction is rolled back."})
        dump(self.folder / "http.json", self.http)
        dump(self.folder / "calls.json", {key: sum(t["call_counts"][key] for t in traces)
             for key in ("logical_model_calls", "provider_attempts", "external_http_calls")})
        transaction.set_rollback(True)
        self.atomic.__exit__(None, None, None)
        self.clock.stop()
        self.scope.disable()

    def db(self):
        return {"bookloans": list(BookLoan.objects.values("pk", "Loan_id", "Book_id", "late_risk", "return_date").order_by("pk")),
                "loans": list(Loan.objects.values("pk", "Customer_id", "loan_date", "due_date").order_by("pk")),
                "plans": list(Customer.objects.values("pk", "name", "reading_plan").order_by("pk"))}

    def traces(self):
        file = self.folder / "ai_invocations.jsonl"
        return [json.loads(s) for s in file.read_text().splitlines()] if file.exists() else []

    def record(self, response, name="response"):
        filename = name + "-" + str(len(self.http)) + ".html"
        (self.folder / filename).write_bytes(response.content)
        self.http.append({"status": response.status_code, "response": filename,
                          "redirects": getattr(response, "redirect_chain", [])})
        return response

    def loan(self, loan_date="2026-06-01", due_date="2026-06-15", return_date="2026-06-20",
             customer=None, book=None, with_book=True):
        loan = Loan.objects.create(Customer=customer or self.bob, loan_date=loan_date,
                                   due_date=due_date)
        if with_book:
            BookLoan.objects.bulk_create([BookLoan(Loan=loan, Book=book or self.books["history"], return_date=return_date, late_risk="NOT_ASSESSED")])
        return loan

    def link_id(self, loan):
        return BookLoan.objects.get(Loan=loan).pk

    def history(self, plan=False, **changes):
        policy = deepcopy((PLAN if plan else RISK)["context"]["history"])
        policy.update(changes)
        return context.retrieve_customer_history(self.bob, policy, as_of=TODAY)

    def clear_history(self):
        Loan.objects.filter(Customer=self.bob).delete()

    def risk(self, book=None, loan=None, **dates):
        loan = loan or self.loan(**{**FIXTURE["current_loan"], **dates}, with_book=False)
        before = BookLoan.objects.count()
        response = self.record(self.staff.post(reverse("librarian:loans_book_loans_create"),
                              {"Loan": loan.pk, "Book": (book or self.books["history"]).pk}), "risk-create")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(BookLoan.objects.count(), before + 1)
        saved = BookLoan.objects.latest("pk")
        return saved, self.traces()[-1]

    def plan(self, data=None, client=None, url=None, follow=True):
        return self.record((client or self.client).post(url or MEMBER_URL,
                           data if data is not None else {ACTION: self.bob.pk}, follow=follow), "plan")

    def counts(self, trace, n):
        self.assertEqual(trace["call_counts"], {"logical_model_calls": n, "provider_attempts": 0, "external_http_calls": 0})

    def test_CFG_01(self):
        validate_metadata(METADATA)
        for config, model, field in ((RISK, "BookLoan", "late_risk"), (PLAN, "Customer", "reading_plan")):
            self.assertEqual(validate_ai_config(config, model, field), config)
            changes = [("trigger.class", "Book"), ("output.write_back", "name"),
                       ("ai_config_version", "1.0"), ("model_profile", "unknown"),
                       ("context.history.completed_only", False), ("context.history.as_of", None),
                       ("context.history.as_of", "wrong")]
            if model == "BookLoan":
                changes += [("trigger.on", "save"), ("template.name", "unknown"),
                            ("template", {"name": "library_late_risk_v3", "chain": []})]
            else:
                changes += [("template.chain", list(reversed(PLAN["template"]["chain"]))),
                            ("template.chain", PLAN["template"]["chain"][:2]),
                            ("template", {"name": "x", "chain": PLAN["template"]["chain"]})]
            for key, value in changes:
                with self.subTest(model=model, key=key, value=value):
                    bad = deepcopy(METADATA)
                    set_path(metadata_config(bad, model, field)["ai_config"], key, value)
                    with self.assertRaisesRegex(GenerationConfigurationError, model + "." + field):
                        validate_metadata(bad)
            with self.assertRaises(ConfigurationError):
                validate_ai_config(config, "Book", field)
        # Prove shell preflight occurs before output creation.
        bad = deepcopy(METADATA)
        metadata_config(bad, "BookLoan", "late_risk")["ai_config"]["ai_config_version"] = "1.0"
        f = self.folder / "bad-metadata.json"
        dump(f, bad)
        rejected_name = ROOT.name + "Rejected"
        run = subprocess.run(["bash", str(GEN / "generator.sh"), "test", ROOT.parent.name, rejected_name, str(f)],
                             capture_output=True, text=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertFalse((ROOT.parent / rejected_name).exists())
        (self.folder / "preflight.log").write_text(run.stdout + run.stderr)
        self.assertEqual(self.traces(), [])

    def test_CFG_02(self):
        cases = [("context.history.limit", v) for v in (0, 51, "10", True)]
        cases += [("context.history.max_scan_records", v) for v in (9, 1001)]
        cases += [("output.reason.required", False), ("output.reason.max_length", 121),
                  ("output.allowed_values", ["LOW", "LOW"]), ("output.allowed_values", ["", "HIGH"]),
                  ("output.allowed_values", ["LOW", "NOT_ASSESSED"]), ("context.history.typo", True)]
        for key, value in cases:
            with self.subTest(key=key, value=value):
                config = deepcopy(RISK)
                set_path(config, key, value)
                with self.assertRaisesRegex(ConfigurationError, "BookLoan.late_risk"):
                    validate_ai_config(config, "BookLoan", "late_risk")
        self.assertEqual(self.traces(), [])

    def render_variant(self, meta, suffix):
        """Use the production application generator and model generator in a new directory."""
        project = ROOT.name + suffix + uuid.uuid4().hex[:6]
        target = ROOT.parent / project
        target.mkdir()
        dump(target / "metadata.json", meta)
        for script, args in [
            ("generate_models.py", [project, str(target / "metadata.json"), "True", ROOT.parent.name]),
            *[("generate_application.py", [project, i["value"]["name"], str(target / "metadata.json"), "True", ROOT.parent.name])
              for i in meta["interfaces"]],
        ]:
            completed = subprocess.run([sys.executable, str(GEN / "generation_scripts" / script)] + args,
                                       capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        return target

    def test_CFG_04(self):
        meta = deepcopy(METADATA)
        config = metadata_config(meta, "BookLoan", "late_risk")["ai_config"]
        config["context"]["history"].update(limit=7, order_by="-loan_date", max_scan_records=333)
        config["output"].update(allowed_values=["SAFE", "RISKY"], on_skip="PENDING")
        config["output"]["reason"]["max_length"] = 77
        config["model_profile"] = "strong"
        target = self.render_variant(meta, "Roundtrip")
        tree = ast.parse((target / "shared_models/ai_hooks.py").read_text())
        actual = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == RISK_KEY for t in n.targets))
        self.assertEqual(actual, config)
        dump(self.folder / "regenerated_config.json", actual)

    def test_CFG_05(self):
        config = deepcopy(RISK)
        config["output"]["allowed_values"] = ["SAFE", "RISKY"]
        with patch.object(ai_hooks, RISK_KEY, config):
            saved, trace = self.risk()
            self.assertEqual(saved.late_risk, "SAFE")
            prompt = trace["prompts"][0]["prompt"]
            self.assertIn('SAFE', prompt)
            self.assertIn('RISKY', prompt)
            self.assertIn("lower", prompt.lower())
            for label in ("LOW", "NOT_ASSESSED", "UNKNOWN"):
                with patch.object(routing, "_fake_content", return_value=json.dumps({"late_risk": label, "reason": "Reason"})):
                    saved, trace = self.risk()
                    self.assertEqual(trace["status"], "parse_error")
                    self.assertFalse(saved.late_risk)

    def test_H_01(self):
        h = self.history()
        expected = FIXTURE["expected_baseline"]
        self.assertIsNone(h.skip_reason)
        self.assertEqual(h.diagnostics["selected_record_ids"], [self.link_id(self.loans[k]) for k in expected["order"]])
        facts = context.compute_facts(h)
        self.assertEqual(facts, {"records": 6, "late_records": 3, "by_category": expected["by_category"]})
        self.assertEqual(len(h.rows), 6)
        dump(self.folder / "history.json", {"diagnostics": h.diagnostics, "rows": h.rows, "facts": facts})

    def test_H_02(self):
        self.clear_history()
        older = self.loan(loan_date="2026-01-01", due_date="2026-01-15", return_date="2026-06-20")
        self.loan(return_date="zzzz")
        self.assertEqual(self.history(limit=1).diagnostics["selected_record_ids"], [self.link_id(older)])
        newer = self.loan(loan_date="2026-06-01", return_date="2026-06-19")
        self.assertEqual(self.history(limit=1).diagnostics["selected_record_ids"], [self.link_id(older)])
        self.assertEqual(self.history(limit=1, order_by="-loan_date").diagnostics["selected_record_ids"], [self.link_id(newer)])
        tie1 = self.loan(return_date="2026-06-20")
        tie2 = self.loan(return_date="2026-06-20")
        self.assertEqual(self.history(limit=2).diagnostics["selected_record_ids"], [self.link_id(tie2), self.link_id(tie1)])
        self.assertEqual(self.history(limit=2, order_by="-loan_date").diagnostics["selected_record_ids"], [self.link_id(tie2), self.link_id(tie1)])

    def test_H_03(self):
        self.clear_history()
        current = self.loan()
        self.loan(customer=self.alice)
        for returned in (None, "", "  "):
            self.loan(return_date=returned)
        for fields, reason in [
            ({"loan_date": "20260101"}, "unparseable"), ({"loan_date": "2026-W01-1"}, "unparseable"),
            ({"due_date": "2026-02-30"}, "unparseable"), ({"due_date": "2026-05-31"}, "due_before_loan"),
            ({"return_date": "2026-05-31"}, "return_before_loan"),
        ]:
            self.loan(**fields)
        h = context.retrieve_customer_history(self.bob, RISK["context"]["history"], as_of=TODAY, exclude_loan_pk=current.pk)
        self.assertEqual(h.diagnostics["candidate_record_count"], 8)
        self.assertEqual(h.diagnostics["not_completed_count"], 3)
        self.assertEqual([r["reason"] for r in h.diagnostics["excluded_rows"]],
                         ["unparseable", "unparseable", "unparseable", "due_before_loan", "return_before_loan"])
        self.assertEqual(context.parse_date(" 2026-01-01 "), date(2026, 1, 1))
        self.assertEqual(h.skip_reason, "no_valid_history")
        dump(self.folder / "diagnostics.json", h.diagnostics)

    def test_H_04(self):
        same = self.loan(return_date=TODAY.isoformat())
        future = self.loan(return_date=(TODAY + timedelta(days=1)).isoformat())
        self.assertEqual(len(self.history().rows), 6)
        plan = self.history(plan=True)
        self.assertEqual(len(plan.rows), 7)
        self.assertIn(self.link_id(same), plan.diagnostics["selected_record_ids"])
        self.assertNotIn(self.link_id(future), plan.diagnostics["selected_record_ids"])
        Loan.objects.filter(pk__in=[l.pk for l in self.loans.values()]).delete()
        saved, trace = self.risk()
        self.assertEqual(trace["skip_reason"], "no_valid_history")
        self.counts(trace, 0)

    def test_H_05(self):
        for kind in ("empty", "unreturned", "invalid", "no_books", "bad_books"):
            self.clear_history()
            if kind == "unreturned": self.loan(return_date=" ")
            if kind == "invalid": self.loan(return_date="bad")
            if kind == "no_books": self.loan(with_book=False)
            if kind == "bad_books":
                book = Book.objects.create(title=" ", category="HISTORY", Author=self.author)
                self.loan(book=book)
            saved, trace = self.risk()
            self.assertEqual(trace["skip_reason"], "empty_history" if kind in ("empty", "unreturned", "no_books") else "no_valid_history")
            self.counts(trace, 0)
            if trace["skip_reason"] == "no_valid_history":
                self.assertTrue(trace["diagnostics"]["excluded_rows"])
        self.clear_history()
        valid = self.loan(return_date="2026-06-19")
        self.loan(return_date="2026-06-20", with_book=False)
        self.assertEqual(self.history(limit=1).diagnostics["selected_record_ids"], [self.link_id(valid)])

    def test_H_06(self):
        self.clear_history()
        loan = self.loan(loan_date="2026-07-01", due_date="2026-07-15", return_date="2026-07-19")
        extra = Book.objects.create(title="Another science", category="SCIENCE", Author=self.author)
        BookLoan.objects.bulk_create([BookLoan(Loan=loan, Book=extra, return_date="2026-07-14"),
            BookLoan(Loan=loan, Book=self.books["science"], return_date="2026-07-15")])
        h = self.history()
        self.assertEqual(context.compute_facts(h), {"records": 3, "late_records": 1, "by_category": {
            "HISTORY": {"records": 1, "late_records": 1, "max_days_overdue": 4},
            "SCIENCE": {"records": 2, "late_records": 0, "max_days_overdue": 0}}})
        with self.assertRaises(IntegrityError), transaction.atomic():
            BookLoan.objects.create(Loan=loan, Book=self.books["history"])
        self.loan()
        self.assertEqual(len(self.history().rows), 4)

    def test_H_07(self):
        self.clear_history()
        loan = self.loan(with_book=False)
        books = Book.objects.bulk_create([Book(title="Budget " + str(i), category="SCIENCE", Author=self.author) for i in range(201)])
        links = BookLoan.objects.bulk_create([BookLoan(Loan=loan, Book=book, return_date="2026-06-14") for book in books])
        h = self.history()
        self.assertEqual((h.skip_reason, h.diagnostics["budget_kind"]), ("history_budget_exceeded", "record_count"))
        BookLoan.objects.filter(pk=links[-1].pk).delete()
        self.assertEqual(len(self.history(limit=50).rows), 50)
        _, trace = self.risk()
        self.counts(trace, 1)
        BookLoan.objects.filter(pk__in=[b.pk for b in links[151:]]).delete()
        h = self.history(limit=50)
        self.assertIsNone(h.skip_reason)
        self.assertEqual(h.diagnostics["candidate_record_count"], 152) # 151 historical plus current unreturned
        self.assertEqual(len(h.rows), 50)

    def test_H_08(self):
        from ai_runtime import templates, chains
        original = templates.render_prompt
        def sized(name, ctx, extra=0):
            prompt = original(name, ctx)
            return prompt + " " * (60000 + extra - len(prompt))
        with patch.object(templates, "render_prompt", side_effect=sized):
            _, trace = self.risk()
            self.assertEqual(trace["status"], "success")
            self.assertEqual(len(trace["prompts"][0]["prompt"]), 60000)
        with patch.object(templates, "render_prompt", side_effect=lambda n, c: sized(n, c, 1)):
            saved, trace = self.risk()
            self.assertEqual(trace["skip_reason"], "prompt_budget_exceeded")
            self.counts(trace, 0)
        def over_second(name, ctx):
            return "x" * 60001 if "recommend" in name else original(name, ctx)
        with patch.object(chains, "render_prompt", side_effect=over_second):
            self.plan()
            trace = self.traces()[-1]
            self.assertEqual(trace["skip_reason"], "prompt_budget_exceeded")
            self.assertEqual(trace["failed_step"], "recommend")
            self.counts(trace, 1)
        h = self.history(limit=2)
        self.assertEqual(context.compute_facts(h)["records"], 2)
        self.assertEqual({row["bookloan_id"] for row in h.rows}, set(h.diagnostics["selected_record_ids"]))

    def test_LR_01(self):
        for key in ("history", "children"):
            saved, trace = self.risk(book=self.books[key])
            self.assertEqual(trace["status"], "success")
            self.assertIn(saved.late_risk, RISK["output"]["allowed_values"])
            self.assertTrue(trace["reason"].strip())
            self.assertLessEqual(len(trace["reason"]), 120)
            self.counts(trace, 1)
            self.assertNotIn("CHILDREN", trace["context"]["by_category"])

    def test_LR_02(self):
        # Direct runtime defense is distinct from the normal page's early refusal.
        for dates, returned, reason in [
            ({"loan_date": "bad"}, "", "invalid_current_dates"),
            ({"due_date": "2026-01-01"}, "", "invalid_current_dates"),
            ({"loan_date": (TODAY + timedelta(days=1)).isoformat()}, "", "invalid_current_dates"),
            ({}, "bad", "outcome_known"), ({}, TODAY.isoformat(), "outcome_known")]:
            loan = self.loan(**{**FIXTURE["current_loan"], **dates}, with_book=False)
            outcome = invoke(RISK, BookLoan(Loan=loan, Book=self.books["history"], return_date=returned), created=True)
            self.assertEqual(outcome.skip_reason, reason)
            self.assertEqual(outcome.calls, [])
        for field in ("title", "category"):
            bad = Book.objects.create(title="New", category="HISTORY", Author=self.author)
            setattr(bad, field, "invalid category" if field == "category" else " ")
            outcome = invoke(RISK, BookLoan(Loan=loan, Book=bad), created=True)
            self.assertEqual(outcome.skip_reason, "invalid_current_record")

    def test_LR_03(self):
        saved, trace = self.risk()
        old = saved.late_risk
        saved.save()
        saved.refresh_from_db()
        self.assertEqual(saved.late_risk, old)
        trace = self.traces()[-1]
        self.assertEqual(trace["skip_reason"], "not_created")
        self.assertFalse(trace["write_back"]["requested"])
        self.counts(trace, 0)
        bad = deepcopy(RISK)
        bad["ai_config_version"] = "1.0"
        with patch.object(ai_hooks, RISK_KEY, bad):
            saved.save()
        self.assertEqual(self.traces()[-1]["error"]["code"], "configuration_error")
        self.counts(self.traces()[-1], 0)

    def test_LR_04(self):
        saved, _ = self.risk()
        url = reverse("librarian:loans_book_loans_update", args=[saved.pk])
        before = self.db()
        for data in ({}, {"Loan": saved.Loan_id, "Book": saved.Book_id}):
            response = self.record(self.staff.post(url, data), "same-association")
            self.assertEqual(response.status_code, 302)
            self.assertEqual(self.traces()[-1]["skip_reason"], "not_created")
        other_loan = self.loans["B01"]
        for data in ({"Loan": other_loan.pk}, {"Book": self.books["children"].pk},
                     {"Loan": ""}, {"Book": "bad"}, {"Loan": "-1"},
                     {"Loan": [str(saved.Loan_id), str(saved.Loan_id)]}):
            count = len(self.traces())
            response = self.record(self.staff.post(url, data), "frozen-association-error")
            self.assertEqual(response.status_code, 200)
            text = response.content.decode()
            self.assertIn("form-errors", text)
            self.assertIn("Demo History Book", text)
            self.assertIn("Loan #" + str(saved.Loan_id), text)
            self.assertIn('class="frozen-association"', text)
            self.assertNotIn('<select name="Loan">', text)
            self.assertEqual(len(self.traces()), count)
            self.assertEqual(self.db(), before)
        BookLoan.objects.filter(pk=saved.pk).update(late_risk=None)
        response = self.record(self.staff.get(LIBRARY_URL, {"instance_id_BookLoan": saved.pk}), "empty-risk-edit")
        self.assertIn("Not assessed", response.content.decode())

    def test_LR_05(self):
        for output in ("not json", json.dumps({"late_risk": "UNKNOWN", "reason": "a"}),
                       json.dumps({"late_risk": "NOT_ASSESSED", "reason": "a"}),
                       json.dumps({"late_risk": "LOW"}),
                       json.dumps({"late_risk": "LOW", "reason": " "}),
                       json.dumps({"late_risk": "LOW", "reason": "a" * 121})):
            with patch.object(routing, "_fake_content", return_value=output):
                saved, trace = self.risk()
            self.assertEqual(trace["status"], "parse_error")
            self.assertFalse(saved.late_risk)
            self.counts(trace, 1)

    def test_LR_06(self):
        for module, name, error, calls in [
            (routing, "_fake_content", RuntimeError("Provider unavailable"), 1),
            (routing, "_fake_content", TimeoutError("Timed out"), 1),
            (context, "build_context", RuntimeError("Context unavailable"), 0),
        ]:
            with patch.object(module, name, side_effect=error):
                saved, trace = self.risk()
            self.assertEqual(trace["status"], "invoke_error")
            self.assertFalse(saved.late_risk)
            self.counts(trace, calls)
        original_open = Path.open
        def log_failure(path, *args, **kwargs):
            if path.name == "ai_invocations.jsonl": raise OSError("Test log unavailable")
            return original_open(path, *args, **kwargs)
        loan = self.loan(**FIXTURE["current_loan"], with_book=False)
        with patch.object(Path, "open", log_failure):
            saved = BookLoan.objects.create(Loan=loan, Book=self.books["history"])
        saved.refresh_from_db()
        self.assertIn(saved.late_risk, RISK["output"]["allowed_values"])
        from django.db.models.query import QuerySet
        with patch.object(QuerySet, "update", side_effect=DatabaseError("Test write-back DB failure")):
            with self.assertRaises(DatabaseError), transaction.atomic():
                BookLoan.objects.create(Loan=loan, Book=self.books["children"])
        trace = self.traces()[-1]
        self.assertEqual(trace["status"], "success")  # Explicitly an AI result, not a commit claim.
        self.assertTrue(trace["write_back"]["requested"])
        self.assertFalse(BookLoan.objects.filter(pk=trace["pk"]).exists())
        self.sdk_timeouts()

    def sdk_timeouts(self):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        from openai import APITimeoutError as OpenAITimeout
        from groq import APITimeoutError as GroqTimeout
        hits = []
        class SlowHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                hits.append(self.path)
                time.sleep(0.5)
                try:
                    self.send_response(200); self.end_headers(); self.wfile.write(b'{}')
                except (BrokenPipeError, ConnectionResetError):
                    pass
            def log_message(self, *args): pass
        server = ThreadingHTTPServer(("127.0.0.1", 0), SlowHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        evidence = []
        try:
            for profile, exception in (("cheap", GroqTimeout), ("strong", OpenAITimeout)):
                spec = {**MODEL_PROFILES[profile], "timeout_s": 0.05}
                counts = {"provider_attempts": 0, "external_http_calls": 0}
                start = time.monotonic()
                prior = len(hits)
                with patch.dict(os.environ, {"OPENAI_API_KEY": "local-test-key", "GROQ_API_KEY": "local-test-key"}):
                    with self.assertRaises(exception):
                        routing._call_provider(spec, "local timeout test", counts,
                            base_url="http://127.0.0.1:" + str(server.server_port) + "/v1")
                elapsed = time.monotonic() - start
                self.assertEqual(len(hits) - prior, 1)
                self.assertEqual(counts, {"provider_attempts": 1, "external_http_calls": 0})
                self.assertLess(elapsed, 2.0)  # Test tolerance only; not a request deadline guarantee.
                evidence.append({"profile": profile, "test_timeout_s": 0.05, "elapsed_s": elapsed, **counts, "local_requests": 1})
        finally:
            server.shutdown()
        dump(self.folder / "sdk-timeouts.json", evidence)

    def test_LR_07(self):
        loan = self.loan(**FIXTURE["current_loan"], with_book=False)
        one, t1 = self.risk(loan=loan)
        two, t2 = self.risk(loan=loan, book=self.books["children"])
        self.assertNotEqual(t1["invocation_id"], t2["invocation_id"])
        self.assertEqual((t1["pk"], t2["pk"]), (one.pk, two.pk))
        for trace in (t1, t2):
            self.counts(trace, 1)
            self.assertNotIn(loan.pk, [row["loan_id"] for row in trace["context"]["history"]])
            self.assertEqual(trace["diagnostics"]["selected_record_count"], 6)

    def test_LR_08(self):
        loan = self.loan(loan_date="2026-04-01", due_date="2026-04-15", with_book=False)
        outcome = invoke(RISK, BookLoan(Loan=loan, Book=self.books["history"]), created=True)
        self.assertEqual(outcome.diagnostics["assessment_mode"], "historical_simulation")
        self.assertEqual(outcome.diagnostics["selected_record_ids"], [self.link_id(self.loans[k]) for k in ("B03", "B02", "B01")])
        self.assertEqual(outcome.context["facts"]["late_records"], 0)

    def test_RP_01(self):
        response = self.record(self.client.get(MEMBER_URL), "own-list")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([c.pk for c in response.context["Customer_list"]], [self.bob.pk])
        self.assertIn("bob@example.com", response.content.decode())
        self.assertNotIn("alice@example.com", response.content.decode())
        self.assertEqual(self.traces(), [])
        response = self.plan()
        self.assertEqual(response.status_code, 200)
        self.assertIn("Your reading plan has been updated", response.content.decode())
        self.bob.refresh_from_db()
        self.assertTrue(self.bob.reading_plan)
        trace = self.traces()[-1]
        self.counts(trace, 3)
        self.assertEqual(trace["write_back"]["intended_value"], self.bob.reading_plan)
        count = len(self.traces())
        self.client.get(MEMBER_URL)
        self.assertEqual(len(self.traces()), count)

    def test_RP_02(self):
        before = self.db()
        for data, status in [
            ({ACTION: self.alice.pk}, 404), ({"custom_Book_x": self.books["history"].pk}, 403),
            ({"custom_Customer_delete": self.bob.pk}, 403),
            ({ACTION: "bad"}, 400), ({ACTION: "0"}, 400), ({ACTION: "-1"}, 400),
            ({ACTION: self.bob.pk, "custom_Book_x": 1}, 400),
            ({ACTION: [str(self.bob.pk), str(self.bob.pk)]}, 400), ({}, 400),
        ]:
            response = self.plan(data, follow=False)
            self.assertEqual(response.status_code, status, data)
        response = self.plan(client=self.staff, url=LIBRARY_URL, follow=False)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.db(), before)
        self.assertEqual(self.traces(), [])

    def test_RP_03(self):
        for email in ("", "missing@example.com"):
            User.objects.filter(pk=self.member.pk).update(email=email)
            response = self.client.get(MEMBER_URL)
            self.assertEqual(list(response.context["Customer_list"]), [])
            self.assertEqual(self.plan(follow=False).status_code, 404)
        User.objects.filter(pk=self.member.pk).update(email=" BOB@EXAMPLE.COM ")
        response = self.client.get(MEMBER_URL)
        self.assertEqual([c.pk for c in response.context["Customer_list"]], [self.bob.pk])
        duplicate = Customer.objects.create(name="duplicate", email=" BOB@example.COM ")
        self.assertEqual(list(self.client.get(MEMBER_URL).context["Customer_list"]), [])
        self.assertEqual(self.plan(follow=False).status_code, 404)
        duplicate.delete()
        extra = User.objects.create(username="duplicate", email="bob@example.com", is_member=True)
        self.assertEqual(list(self.client.get(MEMBER_URL).context["Customer_list"]), [])
        self.assertEqual(self.plan(follow=False).status_code, 404)
        extra.delete()
        self.assertEqual(self.traces(), [])

    def test_RP_04(self):
        from utils.loading_json_utils import get_application_component
        meta = deepcopy(METADATA)
        member = next(i["value"]["data"] for i in meta["interfaces"] if i["value"]["name"] == "member")
        book_node = next(n for d in meta["diagrams"] if d["type"] == "classes"
                         for n in d["nodes"] if n.get("cls", {}).get("name") == "Book")
        member["sections"].insert(0, {"id": "multimodel-books", "name": "books", "text": "Books",
            "class": book_node["cls_ptr"], "attributes": [{"name": "title", "type": "str", "derived": False}],
            "methods": [], "operations": {"create": False, "delete": False, "update": False}})
        member["pages"][0]["sections"].insert(0, {"label": "books", "value": "multimodel-books"})
        target = self.render_variant(meta, "Multimodel")
        namespace = {}
        exec(compile((target / "member/views.py").read_text(), str(target / "member/views.py"), "exec"), namespace)
        view = namespace["member_customers_ListView"]
        self.assertIs(view.model, Book)
        self.assertIs(view.allowed_actions[ACTION][0], Customer)
        module = type(sys)("bl_test_urls")
        module.urlpatterns = importlib.import_module(settings.ROOT_URLCONF).urlpatterns + [path("multi", view.as_view())]
        templates = deepcopy(settings.TEMPLATES)
        templates[0]["DIRS"] = [str(target / "member/templates")]
        with override_settings(ROOT_URLCONF=module, TEMPLATES=templates):
            response = self.record(self.client.get("/multi"), "multi-own-list")
            self.assertEqual(response.status_code, 200)
            self.assertEqual([c.pk for c in response.context["Customer_list"]], [self.bob.pk])
            self.assertEqual(self.plan(url="/multi", follow=False).status_code, 302)
            self.assertEqual(self.plan(url="/multi", data={ACTION: self.alice.pk}, follow=False).status_code, 404)
            edit = self.client.get("/multi", {"instance_id_Customer": self.alice.pk})
            self.assertEqual(edit.status_code, 404)
        # Same scope for parent contexts, including a runtime missing-policy fail-closed.
        rf = RequestFactory().get("/")
        rf.user = self.member
        v = view()
        v.setup(rf)
        v.object_list = v.get_queryset()
        v.parent_models = [Customer]
        self.assertEqual([c.pk for c in v.get_context_data()["parent_Customer_list"]], [self.bob.pk])
        with patch.object(shared_views, "OWNERSHIP", {}):
            self.assertEqual(list(shared_views.scoped_queryset(rf, "member", Customer)), [])
        missing = deepcopy(meta)
        del metadata_config(missing, "Customer", "reading_plan")["ai_config"]
        # BookLoan is also protected but has no member ownership rule.
        md = next(i["value"]["data"] for i in missing["interfaces"] if i["value"]["name"] == "member")
        cls = next(n["cls_ptr"] for d in missing["diagrams"] if d["type"] == "classes"
                   for n in d["nodes"] if n.get("cls", {}).get("name") == "BookLoan")
        md["sections"][0]["class"] = cls
        with self.assertRaisesRegex(GenerationConfigurationError, "requires both late_risk and reading_plan"):
            validate_metadata(missing)
        member["pages"][0]["type"]["value"] = "activity"
        with self.assertRaisesRegex(GenerationConfigurationError, "activity"):
            validate_metadata(meta)

    def test_RP_05(self):
        self.assertEqual(Client().post(MEMBER_URL, {ACTION: self.bob.pk}).status_code, 302)
        csrf = Client(enforce_csrf_checks=True)
        csrf.force_login(self.member)
        self.assertEqual(csrf.post(MEMBER_URL, {ACTION: self.bob.pk}).status_code, 403)
        self.assertEqual(self.client.get(LIBRARY_URL).status_code, 403)
        self.assertEqual(self.staff.get(MEMBER_URL).status_code, 403)
        self.assertEqual(self.traces(), [])

    def test_RP_06(self):
        for old in (None, "Previous plan"):
            for kind, reason in (("empty", "empty_history"), ("invalid", "no_valid_history"),
                                 ("budget", "history_budget_exceeded")):
                self.clear_history()
                if kind == "invalid": self.loan(return_date="bad")
                if kind == "budget":
                    loans = Loan.objects.bulk_create([Loan(Customer=self.bob) for _ in range(201)])
                    BookLoan.objects.bulk_create([BookLoan(Loan=loan, Book=self.books['history']) for loan in loans])
                Customer.objects.filter(pk=self.bob.pk).update(reading_plan=old)
                response = self.plan()
                self.assertIn("No new reading plan was generated", response.content.decode())
                if old: self.assertIn("Your previous plan has been kept", response.content.decode())
                self.bob.refresh_from_db()
                self.assertEqual(self.bob.reading_plan, old or PLAN["output"]["on_skip"])
                trace = self.traces()[-1]
                self.assertEqual(trace["skip_reason"], reason)
                self.counts(trace, 0)

    def test_RP_07(self):
        self.plan()
        trace = self.traces()[-1]
        self.assertIn("Borrowed and returned science and history books", trace["prompts"][1]["prompt"])
        self.assertIn("Demo Recommendation A", trace["prompts"][2]["prompt"])
        Customer.objects.filter(pk=self.bob.pk).update(reading_plan="Previous plan")
        original = routing._fake_content
        def fail_second(purpose, allowed_values=None):
            return "bad JSON" if "recommend" in purpose else original(purpose, allowed_values)
        with patch.object(routing, "_fake_content", side_effect=fail_second):
            response = self.plan()
        self.assertIn("Any existing plan has been kept", response.content.decode())
        trace = self.traces()[-1]
        self.assertEqual((trace["status"], trace["failed_step"]), ("chain_error", "recommend"))
        self.counts(trace, 2)
        self.bob.refresh_from_db()
        self.assertEqual(self.bob.reading_plan, "Previous plan")

    def test_RP_08(self):
        original = routing._fake_content
        good = json.loads(original("reading_plan_sequence_v1"))
        cases = [
            ({**good, "ordered": ["Other", "Demo Recommendation A", "Demo Recommendation C"]}, False),
            ({**good, "ordered": ["Demo Recommendation A"] * 3}, False),
            ({**good, "ordered": good["ordered"][:2]}, False),
            ({**good, "summary": ""}, False), ({**good, "summary": "a" * 256}, False),
            ({**good, "summary": "a" * 255}, True),
        ]
        for output, success in cases:
            Customer.objects.filter(pk=self.bob.pk).update(reading_plan="Previous plan")
            with patch.object(routing, "_fake_content", side_effect=lambda p, allowed_values=None:
                              json.dumps(output) if "sequence" in p else original(p, allowed_values)):
                self.plan()
            trace = self.traces()[-1]
            self.assertEqual(trace["status"], "success" if success else "chain_error")
            self.counts(trace, 3)
            self.bob.refresh_from_db()
            self.assertEqual(self.bob.reading_plan, output["summary"] if success else "Previous plan")
        for purpose, output, expected_step, calls in [
            ("analyze_taste", {"genres": []}, "analyze_taste", 1),
            ("analyze_taste", {"genres": [" "]}, "analyze_taste", 1),
            ("recommend", {"books": ["Same", "same", "Other"]}, "recommend", 2),
        ]:
            with patch.object(routing, "_fake_content", side_effect=lambda p, allowed_values=None:
                              json.dumps(output) if purpose in p else original(p, allowed_values)):
                self.plan()
            trace = self.traces()[-1]
            self.assertEqual(trace["failed_step"], expected_step)
            self.counts(trace, calls)

    def test_GEN_01(self):
        self.assertEqual((SEED["alice_loans"], SEED["bob_loans"]), (5, 8))
        self.assertEqual(set(SEED["history_labels"]), {"NOT_ASSESSED"})
        self.assertEqual(SEED["member_email"], "bob@example.com")
        dump(self.folder / "seed.json", SEED)
        self.assertNotIn("copy_database", (ROOT / ROOT.name / "settings.py").read_text())
        same_day = self.loan(customer=self.alice, **FIXTURE["current_loan"], with_book=False)
        bob_day = self.loan(**FIXTURE["current_loan"], with_book=False)
        response = self.record(self.staff.get(LIBRARY_URL, {"create_book_loans": "true"}), "loan-selector")
        text = response.content.decode()
        for loan, name in ((same_day, "alice"), (bob_day, "bob")):
            self.assertIn('value="' + str(loan.pk) + '">Loan #' + str(loan.pk), text)
            self.assertIn("· " + name + " · " + FIXTURE["current_loan"]["loan_date"], text)
        self.assertIn("Create a borrowing group", text)
        self.assertIn("Not assessed", self.client.get(MEMBER_URL).content.decode())
        self.assertIn(reverse("librarian:loans_loans_create"),
                      self.staff.get(LIBRARY_URL, {"create_loans": "true"}).content.decode())
        self.assertEqual(BookLoan.objects.filter(Loan__Customer=self.bob).exclude(return_date="").count(), 6)

    def test_GEN_02(self):
        for source in ROOT.rglob("*.py"):
            ast.parse(source.read_text())
        call_command("check", verbosity=0)
        original = (ROOT / "shared_models/views.py").read_text()
        swapped = deepcopy(METADATA)
        swapped["interfaces"].reverse()
        target = self.render_variant(swapped, "Swapped")
        self.assertEqual(original, (target / "shared_models/views.py").read_text())
        plain = deepcopy(METADATA)
        for diagram in plain["diagrams"]:
            for node in diagram.get("nodes", []):
                for attr in node.get("cls", {}).get("attributes", []):
                    attr.pop("ai_config", None)
        self.assertFalse(validate_metadata(plain)["library_ai_enabled"])
        target = self.render_variant(plain, "Plain")
        namespace = {}
        exec(compile((target / "shared_models/views.py").read_text(), str(target / "shared_models/views.py"), "exec"), namespace)
        self.assertFalse(namespace["LIBRARY_AI_ENABLED"])
        self.assertEqual(namespace["OWNERSHIP"], {})
        request = RequestFactory().get("/")
        request.user = self.member
        self.assertEqual(namespace["scoped_queryset"](request, "member", Customer).count(), 2)
        for source in target.rglob("*.py"):
            ast.parse(source.read_text())
        self.assertFalse((target / "ai_runtime").exists())

    def test_GEN_03(self):
        before = Loan.objects.count()
        response = self.record(self.staff.post(reverse("librarian:loans_loans_create"),
            {k: v for k, v in {**FIXTURE["current_loan"], "Customer": self.bob.pk}.items() if k != "return_date"}), "create-loan-http")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Loan.objects.count(), before + 1)
        loan = Loan.objects.latest("pk")
        self.assertEqual(loan.Customer_id, self.bob.pk)
        saved, trace = self.risk(loan=loan)
        self.assertEqual(trace["status"], "success")
        response = self.record(self.staff.post(reverse("librarian:loans_book_loans_update", args=[saved.pk]),
                                              {"Book": self.books["children"].pk}), "update-error-http")
        self.assertEqual(response.status_code, 200)
        self.assertIn("cannot be changed", response.content.decode())
        self.assertEqual(self.plan().status_code, 200)
        self.assertEqual(self.plan({ACTION: self.alice.pk}, follow=False).status_code, 404)
        self.assertEqual(self.traces()[-1]["status"], "success")


    def checkout_group(self):
        response = self.staff.post(reverse('librarian:loans_loans_create'), {
            'Customer': self.bob.pk, 'loan_date': timezone.localdate().isoformat(),
            'due_date': (timezone.localdate() + timedelta(days=14)).isoformat()})
        self.assertEqual(response.status_code, 302)
        return Loan.objects.latest('pk')

    def test_LC_01(self):
        loan = self.checkout_group()
        one, _ = self.risk(loan=loan)
        before = self.db(); count = len(self.traces())
        with self.assertRaises(IntegrityError), transaction.atomic():
            BookLoan.objects.create(Loan=loan, Book=one.Book)
        response = self.record(self.staff.post(reverse('librarian:loans_book_loans_create'),
            {'Loan': loan.pk, 'Book': one.Book_id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.db(), before)
        self.assertEqual(len(self.traces()), count)
        self.assertIn('already contains', response.content.decode())
        with django.db.connection.cursor() as cursor:
            constraints = django.db.connection.introspection.get_constraints(cursor, BookLoan._meta.db_table)
        self.assertTrue(constraints['bl_bookloan_loan_book_uniq']['unique'])
        self.assertIn('UniqueConstraint', (ROOT / 'shared_models/models.py').read_text())
        self.assertIn('bl_bookloan_loan_book_uniq', (ROOT / 'shared_models/migrations/0001_initial.py').read_text())

    def test_LC_02(self):
        url = reverse('librarian:loans_loans_create')
        base = {'Customer': self.bob.pk, 'loan_date': TODAY.isoformat(), 'due_date': (TODAY+timedelta(days=14)).isoformat()}
        for change in [{'loan_date':''}, {'due_date':'2026-02-30'}, {'due_date':'2026-01-01'},
                       {'loan_date':(TODAY-timedelta(days=1)).isoformat()}, {'return_date':''},
                       {'Customer':''}, {'loan_date':[TODAY.isoformat(),TODAY.isoformat()]}]:
            before=self.db(); calls=len(self.traces())
            response=self.record(self.staff.post(url,{**base,**change}))
            self.assertEqual(response.status_code,200)
            self.assertEqual(self.db(),before);self.assertEqual(len(self.traces()),calls)
        empty=self.loan(with_book=False)
        response=self.staff.post(reverse('librarian:loans_loans_update',args=[empty.pk]),base)
        self.assertEqual(response.status_code,302)
        empty.refresh_from_db();self.assertEqual(empty.loan_date,TODAY.isoformat())

    def test_LC_03(self):
        old=self.loan(with_book=False)
        current=self.checkout_group()
        bad=Book.objects.create(title='Invalid category',category='science',Author=self.author)
        url=reverse('librarian:loans_book_loans_create')
        for data in [{'Loan':old.pk,'Book':self.books['science'].pk},
                     {'Loan':current.pk,'Book':bad.pk},
                     {'Loan':current.pk,'Book':self.books['science'].pk,'return_date':TODAY.isoformat()},
                     {'Loan':[str(current.pk),str(current.pk)],'Book':self.books['science'].pk},
                     {'Loan':current.pk,'Book':self.books['science'].pk,'return_date':['','']}]:
            before=self.db();calls=len(self.traces())
            response=self.record(self.staff.post(url,data))
            self.assertEqual(response.status_code,200)
            self.assertEqual(self.db(),before);self.assertEqual(len(self.traces()),calls)
        one,_=self.risk(loan=current)
        self.assertEqual(self.staff.post(reverse('librarian:loans_book_loans_update',args=[one.pk]),
            {'return_date':TODAY.isoformat()}).status_code,302)
        calls=len(self.traces())
        response=self.staff.post(url,{'Loan':current.pk,'Book':self.books['science'].pk})
        self.assertEqual(response.status_code,200);self.assertEqual(len(self.traces()),calls)

    def test_LC_04(self):
        loan=self.checkout_group()
        self.assertIn('Awaiting books',self.staff.get(LIBRARY_URL).content.decode())
        one,_=self.risk(loan=loan)
        url=reverse('librarian:loans_loans_update',args=[loan.pk])
        for data in [{'Customer':self.alice.pk},{'due_date':(TODAY+timedelta(days=30)).isoformat()},
                     {'loan_date':(TODAY-timedelta(days=1)).isoformat()}, {'return_date':TODAY.isoformat()}]:
            before=self.db()
            self.assertEqual(self.staff.post(url,data).status_code,200)
            self.assertEqual(self.db(),before)
        self.assertEqual(self.staff.post(url,{}).status_code,302)
        page=self.staff.get(LIBRARY_URL).content.decode()
        self.assertNotIn('name="instance_id_Loan"  value="'+str(loan.pk)+'"',page)

    def test_LC_05(self):
        loan=self.checkout_group();one,_=self.risk(loan=loan)
        url=reverse('librarian:loans_book_loans_update',args=[one.pk]);risk=one.late_risk
        for data in [{}, {'return_date':''}, {'return_date':TODAY.isoformat()}, {'return_date':TODAY.isoformat()}]:
            response=self.record(self.staff.post(url,data));self.assertEqual(response.status_code,302)
            self.counts(self.traces()[-1],0)
        one.refresh_from_db();self.assertEqual(one.late_risk,risk);self.assertEqual(one.return_result,'Returned on time')
        for value in ['', 'bad', '2026-01-01', (TODAY+timedelta(days=1)).isoformat()]:
            before=self.db();count=len(self.traces())
            self.assertEqual(self.staff.post(url,{'return_date':value}).status_code,200)
            self.assertEqual(self.db(),before);self.assertEqual(len(self.traces()),count)
        two,_=self.risk()
        for value in ['2026-01-01','bad',(TODAY+timedelta(days=1)).isoformat()]:
            self.assertEqual(self.staff.post(reverse('librarian:loans_book_loans_update',args=[two.pk]),{'return_date':value}).status_code,200)
        for value, expected in [('', 'Not returned'), ('bad','Data error')]:
            two.return_date=value;self.assertEqual(two.return_result,expected)
        self.assertNotIn('return_result',[f.name for f in BookLoan._meta.fields])

    def test_LC_06(self):
        # Controlled time exercises partial return without weakening normal entry rules.
        loan=self.checkout_group();a,_=self.risk(book=self.books['science'],loan=loan)
        b,_=self.risk(book=self.books['history'],loan=loan)
        with patch('django.utils.timezone.localdate',return_value=TODAY+timedelta(days=12)):
            self.assertEqual(self.staff.post(reverse('librarian:loans_book_loans_update',args=[a.pk]),
                {'return_date':(TODAY+timedelta(days=12)).isoformat()}).status_code,302)
        policy=RISK['context']['history']
        with patch('django.utils.timezone.localdate',return_value=TODAY+timedelta(days=13)):
            next_group=self.checkout_group()
            _,assessment=self.risk(loan=next_group)
        self.assertIn(a.pk,assessment['diagnostics']['selected_record_ids'])
        self.assertNotIn(b.pk,assessment['diagnostics']['selected_record_ids'])
        with patch('django.utils.timezone.localdate',return_value=TODAY+timedelta(days=18)):
            self.assertEqual(self.staff.post(reverse('librarian:loans_book_loans_update',args=[b.pk]),
                {'return_date':(TODAY+timedelta(days=18)).isoformat()}).status_code,302)
            b.refresh_from_db();self.assertEqual(b.return_result,'Returned 4 days late')
        self.counts(self.traces()[-1],0)
        with patch('django.utils.timezone.localdate',return_value=TODAY+timedelta(days=19)):
            last_group=self.checkout_group()
            _,assessment=self.risk(loan=last_group)
        selected={r['bookloan_id']:r for r in assessment['context']['history']}
        self.assertEqual(selected[a.pk]['days_overdue'],0);self.assertEqual(selected[b.pk]['days_overdue'],4)

    def test_LC_07(self):
        self.assertNotIn('return_date',[f.name for f in Loan._meta.fields])
        one,trace=self.risk();self.assertEqual(trace['status'],'success')
        outcome=invoke(RISK,BookLoan(Loan=one.Loan,Book=one.Book,return_date=TODAY.isoformat()),created=True)
        self.assertEqual(outcome.skip_reason,'outcome_known');self.assertEqual(outcome.calls,[])
        page=self.record(self.staff.get(LIBRARY_URL)).content.decode()
        self.assertLess(page.index('<h2>loans</h2>'),page.index('<h2>book_loans</h2>'))
        self.assertNotIn('later saves do not refresh',page)
        self.assertIn('Actual return result',page);self.assertIn('Checkout risk',page)
        self.assertIn('Book borrowed. Checkout risk:',page)
        create=self.staff.get(LIBRARY_URL,{'create_book_loans':'true'}).content.decode()
        self.assertNotIn('name="return_date"',create)
        with patch.object(routing,'_fake_content',return_value='invalid json'):
            failed,_=self.risk()
        feedback=self.staff.get(LIBRARY_URL).content.decode()
        self.assertIn('risk assessment could not be completed',feedback)
        self.assertNotIn('risk assessment could not be completed',self.staff.get(LIBRARY_URL).content.decode())
        url=reverse('librarian:loans_book_loans_update',args=[one.pk])
        self.assertEqual(self.staff.post(url,{'return_result':'fake on time'}).status_code,302)
        one.refresh_from_db();self.assertEqual(one.return_result,'Not returned')


class RealSmoke(Gates):
    def setUp(self):
        super().setUp()
        self.scope.disable()
        self.scope = override_settings(BASE_DIR=ROOT, DEBUG=False)
        self.scope.enable()

    def traces(self):
        file = ROOT / 'ai_invocations.jsonl'
        return [json.loads(line) for line in file.read_text().splitlines()] if file.exists() else []

    def tearDown(self):
        # Keep successful requests and failure observations in this fresh real prototype.
        self.atomic.__exit__(None, None, None)
        dump(self.folder / "db.json", {"before": self.before, "after": self.db(),
             "note": "Real observation: transaction committed; these rows remain in the fresh prototype."})
        dump(self.folder / "http.json", self.http)
        traces = self.traces()
        if (ROOT / 'ai_invocations.jsonl').exists():
            (self.folder / 'ai_invocations.jsonl').write_bytes((ROOT / 'ai_invocations.jsonl').read_bytes())
        dump(self.folder / "calls.json", {key: sum(t["call_counts"][key] for t in traces)
             for key in ("logical_model_calls", "provider_attempts", "external_http_calls")})
        self.clock.stop()
        self.scope.disable()

    def test_REAL_SMOKE(self):
        self.clock.stop()
        os.environ["AI_RUNTIME_FAKE"] = "0"
        today = timezone.localdate()
        checks = []
        try:
            loan = self.checkout_group()
            saved_books = []
            for book in ("science", "history"):
                saved, trace = self.risk(book=self.books[book], loan=loan)
                saved_books.append(saved)
                checks.append({"action": "risk_" + book, "status": trace["status"],
                               "bookloan_id": saved.pk, "db_value": saved.late_risk, "reason": trace["reason"]})
            returned = saved_books[0]
            response = self.record(self.staff.post(reverse('librarian:loans_book_loans_update', args=[returned.pk]),
                {'return_date': today.isoformat()}), 'return-one-book')
            self.assertEqual(response.status_code, 302)
            returned.refresh_from_db()
            self.assertEqual(returned.return_result, 'Returned on time')
            self.assertEqual(returned.late_risk, checks[0]['db_value'])
            self.assertFalse(BookLoan.objects.get(pk=saved_books[1].pk).return_date)
            response = self.plan()
            self.bob.refresh_from_db()
            checks.append({"action": "reading_plan", "status": self.traces()[-1]["status"],
                           "db_value": self.bob.reading_plan, "http_status": response.status_code})
        finally:
            os.environ["AI_RUNTIME_FAKE"] = "1"
            dump(self.folder / "smoke-checks.json", checks)
        traces = self.traces()
        self.assertTrue(all(c["status"] == "success" for c in checks), checks)
        self.assertEqual(len(traces), 4)
        for trace, n in zip(traces, (1, 1, 0, 3)):
            self.assertEqual(trace["call_counts"], {"logical_model_calls": n, "provider_attempts": n, "external_http_calls": n})
        self.assertEqual([t['diagnostics'].get('selected_record_count') for t in (traces[0], traces[1], traces[3])], [6, 6, 7])
        self.assertTrue(all(0 < len(c["reason"]) <= 120 for c in checks[:2]))


class EvidenceResult(unittest.TextTestResult):
    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            RESULTS[test.gate] = {"status": "fail", "error": self._exc_info_to_string(err, test), "evidence": test.gate + "/"}
    def addSuccess(self, test):
        super().addSuccess(test)
        RESULTS[test.gate] = {"status": "pass", "evidence": test.gate + "/", "db": test.gate + "/db.json",
                              "http": test.gate + "/http.json", "calls": test.gate + "/calls.json"}
    def addFailure(self, test, err):
        super().addFailure(test, err)
        RESULTS[test.gate] = {"status": "fail", "error": self._exc_info_to_string(err, test), "evidence": test.gate + "/"}
    def addError(self, test, err):
        super().addError(test, err)
        RESULTS[getattr(test, "gate", str(test))] = {"status": "fail", "error": self._exc_info_to_string(err, test)}
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        RESULTS[test.gate] = {"status": "not_run", "reason": reason}


if __name__ == "__main__":
    if ARGS.mode == "real":
        suite = unittest.TestSuite([RealSmoke("test_REAL_SMOKE")])
    else:
        selected = os.environ.get("BL_GATE_FILTER")
        suite = (unittest.TestSuite(Gates("test_" + name.replace("-", "_")) for name in selected.split(","))
                 if selected else unittest.defaultTestLoader.loadTestsFromTestCase(Gates))
    result = unittest.TextTestRunner(verbosity=2, resultclass=EvidenceResult).run(suite)
    dump(OUT / "results.json", RESULTS)
    sys.exit(0 if result.wasSuccessful() else 1)
