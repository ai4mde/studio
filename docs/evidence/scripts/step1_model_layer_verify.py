"""
Phase 1G' — Model-layer verification WITHOUT full generated-app migration.

WHY THIS IS NOT a generated-app ORM test:
    `shared_models.models` lives inside the GENERATED app
    (generated_prototypes/<system>/LibraryStep1/shared_models/models.py), which is NOT a
    Django app of the studio-api project, and LibraryStep1 has NOT migrated (zero-interface
    config blocks migration). So we CANNOT legitimately run BookLoan.objects.create(...) or
    loan.bookloan_set.all() yet. Those are genuine generated-app runtime ORM tests and must
    wait until the app can migrate (auth + at least one interface).

WHAT THIS DOES (two parts, both valid today):
    Part A — Studio DB ORM verification (run in studio-api):
        the imported Library class graph is correct:
        5 classes + 1 enum + 4 associations, and BookLoan has exactly two incoming
        associations (from Loan and from Book).
    Part B — generated models.py STATIC verification:
        the file produced by the official generator route contains the expected
        BookLoan class with two FKs, Book.Author FK, Loan.Customer FK, and the
        BookCategory enum with five literals. (Static text/AST check — no migration,
        no instantiation.)

It explicitly does NOT claim the generated app runtime is operational.

HOW TO RUN
    Part A (studio-api):
        docker compose exec studio-api sh -lc 'cd /usr/src/model && \
          /usr/src/.venv/bin/python manage.py shell -c "exec(open(\"/tmp/step1_model_layer_verify.py\").read())"'
    Part B needs the generated file readable from where this runs. Easiest: first copy it
    out of the studio-prototypes container to a path this script can read, e.g.
        docker compose cp studio-prototypes:/usr/src/prototypes/generated_prototypes/<SYSTEM_ID>/LibraryStep1/shared_models/models.py /tmp/generated_models.py
        docker compose cp /tmp/generated_models.py studio-api:/tmp/generated_models.py
    then set STEP1_GENERATED_MODELS=/tmp/generated_models.py before running. If the path is
    absent, Part B is SKIPPED with a clear notice (Part A still runs).
"""
import ast
import os

from metadata.models import Project, Classifier, Relation

PROJECT_NAME = os.environ.get("STEP1_PROJECT_NAME", "Library")

# =====================================================================
# Part A — Studio DB ORM verification (the imported Library class graph)
# =====================================================================
print("===== Phase 1G' Part A: Studio DB model-graph verification =====")
project = Project.objects.filter(name=PROJECT_NAME).order_by("-id").first()
assert project is not None, f"project '{PROJECT_NAME}' not found - run the import first"
system = project.systems.all().first()
assert system is not None, "system not found"

classifiers = list(Classifier.objects.filter(system=system))
relations = list(Relation.objects.filter(system=system))
by_id = {c.id: (c.data or {}) for c in classifiers}
name_of = {cid: d.get("name") for cid, d in by_id.items()}

classes = [c for c in classifiers if (c.data or {}).get("type") == "class"]
enums = [c for c in classifiers if (c.data or {}).get("type") == "enum"]

print(f"classes={len(classes)} enum={len(enums)} relations={len(relations)}")
assert len(classes) == 5, f"expected 5 classes, got {len(classes)}"
assert len(enums) == 1, f"expected 1 enum, got {len(enums)}"
assert len(relations) == 4, f"expected 4 relations, got {len(relations)}"

# BookLoan: exactly two INCOMING associations (Loan -> BookLoan, Book -> BookLoan)
bookloan = next((c for c in classes if (c.data or {}).get("name") == "BookLoan"), None)
assert bookloan is not None, "BookLoan classifier not found"
incoming = [r for r in relations if r.target_id == bookloan.id]
incoming_sources = sorted(name_of.get(r.source_id) for r in incoming)
print(f"BookLoan incoming associations from: {incoming_sources}")
assert incoming_sources == ["Book", "Loan"], \
    f"expected BookLoan incoming from Book and Loan, got {incoming_sources}"

# enum literals present in DB
bookcat = enums[0].data or {}
print(f"BookCategory literals (DB): {bookcat.get('literals')}")
assert sorted(bookcat.get("literals", [])) == sorted(
    ["FICTION", "NON_FICTION", "SCIENCE", "HISTORY", "CHILDREN"])
print("Part A PASSED: Library class graph correct; BookLoan has two incoming associations.")

# =====================================================================
# Part B — generated models.py STATIC verification (no migration)
# =====================================================================
gen_path = os.environ.get("STEP1_GENERATED_MODELS", "/tmp/generated_models.py")
print("\n===== Phase 1G' Part B: generated models.py static verification =====")
if not os.path.exists(gen_path):
    print(f"SKIPPED: generated models.py not found at {gen_path}")
    print("  (copy it out of studio-prototypes first; see the docstring.)")
else:
    src = open(gen_path, "r", encoding="utf-8").read()
    tree = ast.parse(src)  # also proves the generated file is syntactically valid

    def class_node(name):
        return next((n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name), None)

    def fk_targets(classdef):
        """field_name -> first positional string arg of models.ForeignKey(...)"""
        out = {}
        for stmt in classdef.body:
            if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Call):
                call = stmt.value
                attr = call.func
                is_fk = isinstance(attr, ast.Attribute) and attr.attr == "ForeignKey"
                if is_fk and call.args and isinstance(call.args[0], ast.Constant):
                    target = call.args[0].value
                    for t in stmt.targets:
                        if isinstance(t, ast.Name):
                            out[t.id] = target
        return out

    bl = class_node("BookLoan")
    assert bl is not None, "BookLoan class not found in generated models.py"
    bl_fks = fk_targets(bl)
    print(f"BookLoan FK fields (generated): {bl_fks}")
    assert bl_fks.get("Loan") == "Loan", "BookLoan.Loan FK missing/incorrect"
    assert bl_fks.get("Book") == "Book", "BookLoan.Book FK missing/incorrect"

    book = class_node("Book")
    assert book is not None and fk_targets(book).get("Author") == "Author", "Book.Author FK missing"
    loan = class_node("Loan")
    assert loan is not None and fk_targets(loan).get("Customer") == "Customer", "Loan.Customer FK missing"

    # BookCategory enum: nested class Category(TextChoices) with 5 members
    category = next((n for n in book.body if isinstance(n, ast.ClassDef) and n.name == "Category"), None)
    assert category is not None, "nested Book.Category enum not found"
    members = [s.targets[0].id for s in category.body
               if isinstance(s, ast.Assign) and isinstance(s.targets[0], ast.Name)]
    print(f"Book.Category members (generated): {members}")
    for lit in ("FICTION", "NON_FICTION", "SCIENCE", "HISTORY", "CHILDREN"):
        assert lit in members, f"missing enum literal {lit}"

    print("Part B PASSED: generated models.py has BookLoan two FKs, Book/Loan FKs, and 5-literal enum.")

print("\n===== Phase 1G' COMPLETE =====")
print("NOTE: this verifies the MODEL LAYER only. It does NOT claim the generated app")
print("runtime is operational; full generated-app migration requires auth + >=1 interface.")