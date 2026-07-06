"""
T1 semantic verification for UI-triggered prototype generation.

Modes:
  semantic        Run from the studio repo root after UI generation.
  smoke_late_risk Run inside the generated prototype's manage.py shell.

Required env for semantic mode:
  T1_PROTOTYPE_NAME       e.g. LibraryT1A
  T1_SYSTEM_ID            Library system UUID

Optional env for semantic mode:
  T1_METADATA_PATH        default docs/evidence/t1_metadata_from_ui.json
  T1_GENERATION_LOG       default docs/evidence/t1_generation.log
  T1_SHOWMIGRATIONS_LOG   default docs/evidence/t1_showmigrations.log
  T1_GENERATED_ROOT       default prototypes/generated_prototypes
  T1_STEP8_EVIDENCE       default docs/evidence
"""
from __future__ import annotations

import ast
import json
import os
import re
from pathlib import Path


MODE = os.environ.get("T1_MODE", "semantic")


def ok(label: str, message: str) -> None:
    print(f"[PASS] {label}: {message}")


def fail(message: str) -> None:
    raise AssertionError(message)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def iter_class_nodes(metadata: dict):
    for diagram in metadata.get("diagrams", []):
        if diagram.get("type") != "classes":
            continue
        for node in diagram.get("nodes", []):
            cls = node.get("cls") or {}
            yield node, cls


def find_attr(metadata: dict, class_name: str, attr_name: str) -> dict:
    for _, cls in iter_class_nodes(metadata):
        if cls.get("type") != "class" or cls.get("name") != class_name:
            continue
        for attr in cls.get("attributes", []):
            if attr.get("name") == attr_name:
                return attr
    fail(f"{class_name}.{attr_name} missing in metadata")


def assert_v1_metadata(metadata: dict, generation_log: str) -> None:
    late = find_attr(metadata, "BookLoan", "late_risk")
    reading_plan = find_attr(metadata, "Customer", "reading_plan")
    assert late.get("ai_config", {}).get("trigger", {}).get("type") == "post_save", late
    assert (
        reading_plan.get("ai_config", {}).get("trigger", {}).get("type")
        == "user_action"
    ), reading_plan

    interfaces = metadata.get("interfaces")
    assert isinstance(interfaces, list) and interfaces, "metadata.interfaces empty/missing"
    bad = [
        item
        for item in interfaces
        if not isinstance(item, dict)
        or "label" not in item
        or not isinstance(item.get("value"), dict)
    ]
    assert not bad, f"interfaces lost {{label, value}} wrapper: {bad[:2]}"
    assert any(
        item.get("value", {}).get("name") == "librarian" for item in interfaces
    ), "metadata.interfaces does not contain value.name == 'librarian'"
    assert metadata.get("useAuthentication") is True, "useAuthentication is not true"

    required_lines = [
        ("BookLoan", "late_risk"),
        ("Customer", "reading_plan"),
    ]
    for model, attr in required_lines:
        needle = f"[AI4MDE][ai_config] model={model} attribute={attr}"
        assert needle in generation_log, f"generation log missing {needle}"
    assert (
        "[AI4MDE][ai_config] detected 2 AI-managed attribute(s)" in generation_log
    ), "generation log did not report exactly 2 AI-managed attributes"
    ok("V1", "metadata and generator detection both carry late_risk + reading_plan ai_config")


def expected_ai_runtime_files(step8_evidence: Path, step8_runtime_dir: Path | None = None) -> set[str]:
    if step8_runtime_dir and step8_runtime_dir.is_dir():
        return {
            str(path.relative_to(step8_runtime_dir))
            for path in step8_runtime_dir.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        }

    files = set()
    for path in step8_evidence.glob("step8_app_ai_runtime_*.py"):
        suffix = path.name.removeprefix("step8_app_ai_runtime_")
        files.add("__init__.py" if suffix == "__init__.py" else suffix)
    for path in step8_evidence.glob("step8_app_prompt_*.j2"):
        files.add(f"prompt_templates/{path.name.removeprefix('step8_app_prompt_')}")
    return files


def actual_ai_runtime_files(generated_dir: Path) -> set[str]:
    runtime_dir = generated_dir / "ai_runtime"
    return {
        str(path.relative_to(runtime_dir))
        for path in runtime_dir.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }


def assert_v2_artifacts(
    generated_dir: Path, step8_evidence: Path, step8_runtime_dir: Path | None = None
) -> None:
    assert (generated_dir / "shared_models" / "ai_hooks.py").is_file(), "ai_hooks.py missing"
    assert (generated_dir / "shared_models" / "ai_actions.py").is_file(), "ai_actions.py missing"
    assert (generated_dir / "ai_runtime").is_dir(), "ai_runtime/ missing"

    expected = expected_ai_runtime_files(step8_evidence, step8_runtime_dir)
    actual = actual_ai_runtime_files(generated_dir)
    assert actual == expected, {
        "missing": sorted(expected - actual),
        "extra": sorted(actual - expected),
    }
    ok("V2", f"AI artifact set present; ai_runtime files={sorted(actual)}")


def parse_file(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def receiver_senders(tree: ast.Module) -> list[str]:
    senders = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            func = dec.func
            if not (
                isinstance(func, ast.Name)
                and func.id == "receiver"
                or isinstance(func, ast.Attribute)
                and func.attr == "receiver"
            ):
                continue
            for keyword in dec.keywords:
                if keyword.arg == "sender" and isinstance(keyword.value, ast.Name):
                    senders.append(keyword.value.id)
    return senders


def has_customer_reading_plan_attach(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if (
                isinstance(target, ast.Attribute)
                and target.attr == "generate_reading_plan"
                and isinstance(target.value, ast.Name)
                and target.value.id == "Customer"
            ):
                return True
    return False


def assert_v3_trigger_split(generated_dir: Path) -> None:
    hooks_path = generated_dir / "shared_models" / "ai_hooks.py"
    actions_path = generated_dir / "shared_models" / "ai_actions.py"
    hooks_src = hooks_path.read_text(encoding="utf-8")
    actions_src = actions_path.read_text(encoding="utf-8")
    hooks_tree = ast.parse(hooks_src, filename=str(hooks_path))
    actions_tree = ast.parse(actions_src, filename=str(actions_path))

    senders = receiver_senders(hooks_tree)
    assert senders == ["BookLoan"], f"post_save receivers must be only BookLoan, got {senders}"
    assert "reading_plan" not in hooks_src, "reading_plan leaked into ai_hooks.py"
    assert "sender=Customer" not in hooks_src, "Customer receiver leaked into ai_hooks.py"

    assert has_customer_reading_plan_attach(actions_tree), (
        "Customer.generate_reading_plan attach missing in ai_actions.py"
    )
    assert "late_risk" not in actions_src, "late_risk leaked into ai_actions.py"
    ok("V3", "post_save and user_action triggers are split correctly")


def class_def(tree: ast.Module, name: str) -> ast.ClassDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    fail(f"class {name} missing")


def assignment_names(class_node: ast.ClassDef) -> set[str]:
    names = set()
    for stmt in class_node.body:
        if isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
    return names


def fk_targets(class_node: ast.ClassDef) -> dict[str, str]:
    out = {}
    for stmt in class_node.body:
        if not isinstance(stmt, ast.Assign) or not isinstance(stmt.value, ast.Call):
            continue
        call = stmt.value
        if not isinstance(call.func, ast.Attribute) or call.func.attr != "ForeignKey":
            continue
        if not call.args or not isinstance(call.args[0], ast.Constant):
            continue
        for target in stmt.targets:
            if isinstance(target, ast.Name):
                out[target.id] = call.args[0].value
    return out


def enum_literals(book_class: ast.ClassDef) -> set[str]:
    for stmt in book_class.body:
        if isinstance(stmt, ast.ClassDef) and stmt.name == "Category":
            return {
                sub.targets[0].id
                for sub in stmt.body
                if isinstance(sub, ast.Assign)
                and sub.targets
                and isinstance(sub.targets[0], ast.Name)
            }
    return set()


def canonical_domain_class(tree: ast.Module, name: str) -> list[str]:
    node = class_def(tree, name)
    return sorted(
        ast.dump(stmt, annotate_fields=True, include_attributes=False)
        for stmt in node.body
        if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant))
    )


def assert_v4_models(generated_dir: Path, step8_evidence: Path) -> None:
    models_path = generated_dir / "shared_models" / "models.py"
    tree = parse_file(models_path)
    step8_tree = parse_file(step8_evidence / "step8_app_models.py")

    domain = ["Author", "Book", "Customer", "Loan", "BookLoan"]
    for name in domain:
        class_def(tree, name)
    book = class_def(tree, "Book")
    assert enum_literals(book) == {
        "FICTION",
        "NON_FICTION",
        "SCIENCE",
        "HISTORY",
        "CHILDREN",
    }, "Book.Category enum literals mismatch"

    bookloan = class_def(tree, "BookLoan")
    assert "late_risk" in assignment_names(bookloan), "BookLoan.late_risk missing"
    assert fk_targets(bookloan) == {
        "Book": "Book",
        "Loan": "Loan",
    }, f"BookLoan FK mismatch: {fk_targets(bookloan)}"
    customer = class_def(tree, "Customer")
    assert "reading_plan" in assignment_names(customer), "Customer.reading_plan missing"

    diffs = []
    for name in domain:
        actual = canonical_domain_class(tree, name)
        expected = canonical_domain_class(step8_tree, name)
        if actual != expected:
            diffs.append(name)
    assert not diffs, f"domain class-body mismatch vs step8 evidence: {diffs}"

    user_node = next((n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "User"), None)
    user_fields = sorted(assignment_names(user_node)) if user_node else []
    ok(
        "V4",
        "domain models match step8 order-independently; "
        f"observed auth-only User fields={user_fields}",
    )


def assert_v5_migrations(showmigrations_log: str, generation_log: str) -> None:
    assert "Failed to generate prototype" not in generation_log, "generation log contains failure"
    assert "Generated " in generation_log or "POST /generate" in generation_log, (
        "generation log does not show successful generate request"
    )

    checked = []
    current_app = None
    for line in showmigrations_log.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if not stripped.startswith("["):
            current_app = stripped
            continue
        if current_app in {"shared_models", "workflow_engine"}:
            checked.append((current_app, stripped))
            assert stripped.startswith("[X]"), f"unapplied migration: {current_app} {stripped}"
    assert checked, "no shared_models/workflow_engine migrations found in showmigrations log"
    ok("V5", f"all checked migrations applied: {checked}")


def run_semantic() -> None:
    prototype_name = os.environ.get("T1_PROTOTYPE_NAME")
    system_id = os.environ.get("T1_SYSTEM_ID")
    assert prototype_name, "T1_PROTOTYPE_NAME is required"
    assert system_id, "T1_SYSTEM_ID is required"

    metadata_path = Path(os.environ.get("T1_METADATA_PATH", "docs/evidence/t1_metadata_from_ui.json"))
    generation_log_path = Path(os.environ.get("T1_GENERATION_LOG", "docs/evidence/t1_generation.log"))
    showmigrations_path = Path(
        os.environ.get("T1_SHOWMIGRATIONS_LOG", "docs/evidence/t1_showmigrations.log")
    )
    generated_root = Path(os.environ.get("T1_GENERATED_ROOT", "prototypes/generated_prototypes"))
    step8_evidence = Path(os.environ.get("T1_STEP8_EVIDENCE", "docs/evidence"))
    generated_dir = generated_root / system_id / prototype_name
    step8_runtime_dir = Path(
        os.environ.get(
            "T1_STEP8_RUNTIME_DIR",
            str(generated_root / system_id / "LibraryStep8" / "ai_runtime"),
        )
    )

    metadata = load_json(metadata_path)
    generation_log = generation_log_path.read_text(encoding="utf-8")
    showmigrations_log = showmigrations_path.read_text(encoding="utf-8")
    assert generated_dir.is_dir(), f"generated prototype dir missing: {generated_dir}"

    assert_v1_metadata(metadata, generation_log)
    assert_v2_artifacts(generated_dir, step8_evidence, step8_runtime_dir)
    assert_v3_trigger_split(generated_dir)
    assert_v4_models(generated_dir, step8_evidence)
    assert_v5_migrations(showmigrations_log, generation_log)
    print("[DONE] T1 semantic gates V1-V5 PASS.")


def run_smoke_late_risk() -> None:
    import json as _json
    from pathlib import Path as _Path

    from django.conf import settings

    from shared_models.models import Author, Book, BookLoan, Customer, Loan

    assert os.environ.get("AI_RUNTIME_FAKE") == "1", "AI_RUNTIME_FAKE=1 is required"
    log_path = _Path(settings.BASE_DIR) / "ai_invocations.jsonl"
    if log_path.exists():
        log_path.unlink()

    author = Author.objects.create(name="T1 Writer", nationality="NL")
    book = Book.objects.create(title="T1 Test Book", Author=author)
    customer = Customer.objects.create(name="T1 Reader", email="t1@example.com")
    loan = Loan.objects.create(
        loan_date="2026-01-01",
        due_date="2026-01-15",
        return_date="",
        Customer=customer,
    )
    bookloan = BookLoan.objects.create(Loan=loan, Book=book)
    bookloan.refresh_from_db()
    print(f"[smoke] BookLoan pk={bookloan.pk} late_risk={bookloan.late_risk!r}")
    assert bookloan.late_risk == "LOW", f"expected fake LOW, got {bookloan.late_risk!r}"

    assert log_path.exists(), "ai_invocations.jsonl not created"
    lines = [line for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 1, f"expected exactly 1 invocation, got {len(lines)}"
    record = _json.loads(lines[0])
    assert record["event"] == "invoke", record
    assert record["trigger"] == "post_save", record
    assert record["model"] == "BookLoan", record
    assert record["write_back"]["field"] == "late_risk", record
    assert record["write_back"]["value"] == "LOW", record
    assert record["mode"] == "fake", record
    ok("V6", "fake post_save runtime writes BookLoan.late_risk='LOW'")
    print("[DONE] T1 late_risk runtime smoke PASS.")


if MODE == "semantic":
    run_semantic()
elif MODE == "smoke_late_risk":
    run_smoke_late_risk()
else:
    fail(f"unknown T1_MODE={MODE!r}")
