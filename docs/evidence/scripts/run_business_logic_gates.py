#!/usr/bin/env python3
"""Reproducible Library gates. Host Python 3.9+; generation/tests use the service."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

STUDIO = Path(__file__).resolve().parents[3]
SOURCE_DIRS = ["prototypes/backend/generation", "frontend/src/lib/features/diagram/components/modals/EditNodeModal/components/EditAttributes"]
PROTOTYPE_ROOT = STUDIO / "prototypes" / "generated_prototypes"
COMPOSE_FILE = STUDIO / "docker-compose.yaml"
COMPOSE = ["docker", "compose", "-f", str(COMPOSE_FILE)]
SERVICE = "studio-prototypes"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes():
    files = {}
    for folder in SOURCE_DIRS:
        for path in sorted((STUDIO / folder).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                files[str(path.relative_to(STUDIO))] = sha(path)
    files[str(Path(__file__).relative_to(STUDIO))] = sha(Path(__file__))
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--case-data", type=Path, required=True)
    parser.add_argument("--mode", choices=["fake", "real"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--validation-scope", choices=["business", "full"], default="full")
    args = parser.parse_args()
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    token = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    # The output is always a container of immutable runs, including the first run.
    out = args.output.resolve() / ("run_" + token)
    out.mkdir(parents=True, exist_ok=False)
    hashes = source_hashes()
    fingerprint = {"source": hashes, "metadata": sha(args.metadata), "case_data": sha(args.case_data), "compose": sha(COMPOSE_FILE), "validation_scope": args.validation_scope}
    manifest = {"started_at": datetime.now(timezone.utc).isoformat(), "mode": args.mode, "status": "not_run",
                "fingerprint": fingerprint, "commands": [], "output": str(out),
                "old_database_copied": False, "validation_scope": args.validation_scope,
                "pending": [] if args.validation_scope == "full" else ["Studio frontend tests and build"]}
    manifest_path = out / "manifest.json"
    def save():
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    def run(command, label, cwd=None):
        manifest["commands"].append({"label": label, "argv": command})
        save()
        print(label, flush=True)
        with (out / (label + ".log")).open("w") as stream:
            completed = subprocess.run(command, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT)
        if completed.returncode:
            raise RuntimeError(label + " failed; see " + str(out / (label + ".log")))
    try:
        if args.mode == "real":
            # Require the same source and input revision, not merely an old successful log.
            candidates = sorted(args.output.resolve().parent.glob("fake/**/manifest.json"),
                                key=lambda p: p.stat().st_mtime, reverse=True)
            prior = next((p for p in candidates if p.exists()
                          and (lambda m: m.get("status") == "pass" and m.get("fingerprint") == fingerprint)(
                              json.loads(p.read_text()))), None)
            if prior is None:
                raise RuntimeError("real smoke requires a passing fake manifest for exactly these sources and inputs")
            manifest["fake_prerequisite"] = str(prior)
        run(COMPOSE + ["exec", "-T", "-e", "PYTHONDONTWRITEBYTECODE=1", SERVICE, "python", "-c",
                       "import sys,django,openai,groq,httpx,pydantic,jinja2,json; print(json.dumps(dict(python=sys.version,django=django.__version__,openai=openai.__version__,groq=groq.__version__,httpx=httpx.__version__,pydantic=pydantic.__version__,jinja2=jinja2.__version__)))"],
            "dependencies")
        project = "LibraryBL_" + uuid.uuid4().hex[:12]
        system = "bl_v12_" + token
        prototype = "/usr/src/prototypes/generated_prototypes/" + system + "/" + project
        scratch = "/tmp/" + system
        manifest.update(prototype_path=prototype, prototype_host_path=str(PROTOTYPE_ROOT / system / project))
        run(COMPOSE + ["exec", "-T", "-e", "PYTHONDONTWRITEBYTECODE=1", SERVICE, "mkdir", "-p", scratch + "/evidence"], "prepare")
        for src, name in [(args.metadata, "metadata.json"), (args.case_data, "fixture.json")]:
            shutil.copy2(src, out / name)
            run(COMPOSE + ["cp", str(src.resolve()), SERVICE + ":" + scratch + "/" + name], "copy_" + name)
        run(COMPOSE + ["exec", "-T", "-e", "PYTHONDONTWRITEBYTECODE=1", "-e", "AI_RUNTIME_FAKE=1", SERVICE, "bash",
                       "/usr/src/prototypes/backend/generation/generator.sh", system, system, project, scratch + "/metadata.json"], "generate")
        if args.mode == "fake" and args.validation_scope == "full":
            run(["npx", "tsc", "--noEmit"], "frontend_types", STUDIO / "frontend")
            run(["npx", "vite", "build", "--outDir", str(out / "frontend_dist")], "frontend_build", STUDIO / "frontend")
            run(["npx", "vitest", "run",
                 "src/lib/features/diagram/components/modals/EditNodeModal/components/EditAttributes/AiConfigSection.test.tsx",
                 "--cache=false", "--reporter=json", "--outputFile=" + str(out / "frontend_tests.json")],
                "frontend_tests", STUDIO / "frontend")
        test_command = COMPOSE + ["exec", "-T", "-e", "PYTHONDONTWRITEBYTECODE=1", "-e", "AI_RUNTIME_FAKE=1", SERVICE, "python",
            "/usr/src/prototypes/backend/generation/tests/business_logic_gates.py",
            "--prototype", prototype, "--metadata", scratch + "/metadata.json", "--case-data", scratch + "/fixture.json",
            "--output", scratch + "/evidence", "--mode", args.mode]
        try:
            run(test_command, "business_gates")
        finally:
            run(COMPOSE + ["cp", SERVICE + ":" + scratch + "/evidence/.", str(out)], "collect")
        if source_hashes() != hashes or sha(args.metadata) != fingerprint['metadata'] or sha(args.case_data) != fingerprint['case_data']:
            raise RuntimeError('Sources or inputs changed during validation; this run cannot certify that fingerprint')
        results = json.loads((out / "results.json").read_text())
        if args.mode == "fake" and args.validation_scope == "full":
            results["CFG-03"] = {"status": "pass", "evidence": "frontend_tests.json", "db": "N/A", "trace": "N/A"}
            results["CFG-04"]["frontend"] = "frontend_tests.json"
            results["GEN-02"]["frontend_build"] = "frontend_build.log"
        (out / "results.json").write_text(json.dumps(results, indent=2))
        manifest["status"] = "pass" if all(v["status"] == "pass" for v in results.values()) else "fail"
        if manifest["status"] != "pass":
            raise RuntimeError("One or more gates failed or did not run")
    except Exception as exc:
        manifest["status"] = "fail"
        manifest["error"] = str(exc)
        print(str(exc), file=sys.stderr)
    finally:
        manifest["finished_at"] = datetime.now(timezone.utc).isoformat()
        save()
        print("Evidence: " + str(out), flush=True)
    return 0 if manifest["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
