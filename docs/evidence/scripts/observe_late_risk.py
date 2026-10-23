#!/usr/bin/env python3
"""Read one generated Library's trace and SQLite DB without invoking AI or writing data."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3


def observe(prototype, bookloan_id=None, invocation_id=None, include_prompt=False):
    prototype = Path(prototype).resolve()
    database = prototype / "db.sqlite3"
    trace_path = prototype / "ai_invocations.jsonl"
    if not database.is_file():
        raise ValueError("No db.sqlite3 at the explicitly selected prototype")
    records = []
    if trace_path.exists():
        for number, line in enumerate(trace_path.read_text().splitlines(), 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Incomplete/invalid trace line {number}; wait for the request to finish") from exc
            if record.get("model") == "BookLoan":
                records.append(record)
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        columns = {row[1] for row in db.execute('PRAGMA table_info(shared_models_bookloan)')}
        per_book = 'return_date' in columns
        outcome_column = 'bl.return_date' if per_book else 'l.return_date'
        rows = db.execute(f'''
            SELECT bl.id AS bookloan_id, bl.late_risk, l.id AS loan_id,
                   l.loan_date, l.due_date, {outcome_column} AS return_date, c.name AS customer,
                   b.title, b.category
            FROM shared_models_bookloan bl
            JOIN shared_models_loan l ON l.id = bl.Loan_id
            JOIN shared_models_customer c ON c.id = l.Customer_id
            JOIN shared_models_book b ON b.id = bl.Book_id
            ORDER BY bl.id
        ''').fetchall()
    result = {"observed_at": datetime.now(timezone.utc).isoformat(),
              "prototype": str(prototype), "database": str(database),
              "return_unit": "book_loan" if per_book else "legacy_shared_loan",
              "scope": "Read-only current DB snapshot plus recorded trace; browser appearance is not observed."}
    if bookloan_id is None:
        result["rows"] = [dict(row) for row in rows]
        result["events"] = [{k: r.get(k) for k in (
            "pk", "invocation_id", "timestamp", "created", "status", "skip_reason", "mode", "call_counts")}
            for r in records]
        return result
    row = next((dict(r) for r in rows if r["bookloan_id"] == bookloan_id), None)
    if row is None:
        raise ValueError(f"BookLoan {bookloan_id} is absent from this prototype")
    events = [r for r in records if r.get("pk") == bookloan_id]
    if invocation_id:
        candidates = [r for r in events if r.get("invocation_id") == invocation_id]
        if len(candidates) != 1:
            raise ValueError("Select exactly one invocation belonging to this BookLoan")
    else:
        candidates = [r for r in events if r.get("created") is True]
        if len(candidates) > 1:
            raise ValueError("Multiple creation records; select --invocation-id explicitly")
    result["db_now"] = row
    result["events_for_this_bookloan"] = [{k: r.get(k) for k in (
        "invocation_id", "timestamp", "created", "status", "skip_reason", "mode", "call_counts")}
        for r in events]
    record = candidates[0] if candidates else None
    if record is None:
        result["assessment"] = None
        result["notice"] = "No creation trace. A stored label alone does not establish an AI assessment."
        return result
    result["assessment"] = {k: record.get(k) for k in (
        "invocation_id", "timestamp", "created", "status", "skip_reason", "error", "mode",
        "as_of", "assessment_mode", "ai_config_version", "config_sha256", "diagnostics",
        "context", "parsed_output", "reason", "calls", "call_counts")}
    result["assessment"]["prompts"] = [
        {k: v for k, v in prompt.items() if include_prompt or k != "prompt"}
        for prompt in record.get("prompts", [])]
    intended = record.get("write_back", {})
    result["write_intent"] = intended
    result["db_matches_intended_now"] = (
        row["late_risk"] == intended.get("intended_value") if intended.get("requested") else None)
    result["interpretation"] = (
        "write_intent is not proof of persistence. db_now was independently queried after the request; "
        "equality does not prove this invocation caused the value. Compare before/after captures. "
        "Dates shown are the current database values; assessment.as_of is the recorded historical cutoff. "
        "BL-1.2 freezes the shared borrowing period after the first book is added.")
    result["generated_source_sha256"] = {
        str(p.relative_to(prototype)): hashlib.sha256(p.read_bytes()).hexdigest()
        for folder in (prototype / "ai_runtime", prototype / "shared_models")
        for p in sorted(folder.rglob("*"))
        if p.is_file() and p.suffix in {".py", ".j2"}}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prototype", type=Path, required=True)
    parser.add_argument("--bookloan-id", type=int)
    parser.add_argument("--invocation-id")
    parser.add_argument("--prompt", action="store_true")
    args = parser.parse_args()
    if args.invocation_id and args.bookloan_id is None:
        parser.error("--invocation-id requires --bookloan-id")
    try:
        result = observe(args.prototype, args.bookloan_id, args.invocation_id, args.prompt)
    except (ValueError, OSError, sqlite3.Error) as exc:
        parser.exit(1, str(exc) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
