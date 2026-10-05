"""Portable, read-only content verification for the unchanged Code evaluator v8."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import platform
import sys
import tarfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
FREEZE = REPO / "evaluation/friedrich_code_v3/freeze/thesis_final_v8_20261005"
ADDENDUM = Path(__file__).resolve().parent / "runtime_addendum/friedrich_v3/compatibility_v3.json"
ADDENDUM_SHA256 = "52d744c7fd01b7a569ccc8e8c2482dfebc9eb56db5983865616922521532692b"
BRANCH_SCOPE_SHA256 = "1bab86be0191adf14eff8eca15f181c28417c90f2a8e3470568b179b2e6d5bba"


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def original_root(manifest: dict) -> Path:
    before, marker, _ = manifest["validated_run"].partition("/evaluation/friedrich_code_v3/results/")
    require(bool(marker), "unrecognized validated-run path")
    return Path(before)


def local_path(original: str, manifest: dict) -> Path:
    old = original_root(manifest)
    path = Path(original)
    require(path.is_relative_to(old), f"path is not inside the original repository: {original}")
    return REPO / path.relative_to(old)


def checked_manifest() -> dict:
    path = FREEZE / "final_code_v8_freeze_manifest.json"
    sidecar = (FREEZE / "final_code_v8_freeze_manifest.sha256").read_text().split()[0]
    require(sha(path) == sidecar, "freeze manifest SHA-256 mismatch")
    manifest = json.loads(path.read_text())
    require(manifest["evaluator_version"] == "friedrich-code-combined-construct-candidate/8", "wrong evaluator version")
    require(manifest["validated_candidate_count"] == 120 and manifest["validated_case_count"] == 40, "wrong cohort size")
    return manifest


def verify_archive(manifest: dict) -> dict[str, bytes]:
    archive = FREEZE / Path(manifest["sibling_archive"]["path"]).name
    require(sha(archive) == manifest["sibling_archive"]["sha256"], "sibling archive mismatch")
    old_sibling = original_root(manifest).parent / "studio-semantic-v2"
    expected = {str(Path(f["path"]).relative_to(old_sibling)): f["sha256"]
                for f in manifest["files"] if f["scope"] == "studio-semantic-v2"}
    contents: dict[str, bytes] = {}
    with tarfile.open(archive, "r:gz") as stream:
        members = stream.getmembers()
        require(len(members) == manifest["sibling_archive"]["member_count"] == len(expected),
                "sibling archive member count mismatch")
        for member in members:
            require(member.isfile(), f"archive has a non-file member: {member.name}")
            parts = Path(member.name).parts
            require(len(parts) > 1 and parts[0] == "studio-semantic-v2" and ".." not in parts,
                    f"unsafe archive member: {member.name}")
            relative = str(Path(*parts[1:]))
            require(relative in expected and relative not in contents, f"unexpected archive member: {relative}")
            data = stream.extractfile(member).read()
            require(hashlib.sha256(data).hexdigest() == expected[relative], f"archive content changed: {relative}")
            contents[relative] = data
    require(set(contents) == set(expected), "archive does not contain the exact frozen sibling set")
    require(sha(ADDENDUM) == ADDENDUM_SHA256, "compatibility taxonomy addendum mismatch")
    return contents


def verify_environment(manifest: dict) -> dict:
    frozen = manifest["environment"]
    require(sys.version == frozen["python_version"], "Python version differs from validated run")
    require(platform.platform() == frozen["platform"], "platform differs from validated run")
    require(sha(Path(sys._base_executable)) == frozen["executable_sha256"], "Python interpreter hash differs")
    for item in frozen["packages"]:
        installed = importlib.metadata.distribution(item["name"])
        metadata = installed.read_text("METADATA")
        require(installed.version == item["version"] and metadata is not None and
                hashlib.sha256(metadata.encode()).hexdigest() == item["metadata_sha256"],
                f"package identity differs: {item['name']}")
    return {"python": sys.version.split()[0], "platform": platform.platform(),
            "package_metadata_verified": len(frozen["packages"])}


def verify_model(manifest: dict, snapshot: Path | None) -> dict:
    model = manifest["model"]
    if snapshot is None:
        snapshot = Path(model["snapshot_path"])
    require(snapshot.is_dir(), f"pinned model snapshot unavailable: {snapshot}")
    require(snapshot.name == model["revision"], "model snapshot revision directory differs")
    for item in model["files"]:
        path = snapshot / item["relative_path"]
        require(path.is_file() and path.stat().st_size == item["size_bytes"] and sha(path) == item["sha256"],
                f"pinned model mismatch: {item['relative_path']}")
    canonical = json.dumps(model["files"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    require(hashlib.sha256(canonical).hexdigest() == model["tree_sha256"], "model manifest tree digest mismatch")
    return {"snapshot": str(snapshot), "revision": model["revision"],
            "files_verified": len(model["files"])}


def verify_roster(manifest: dict) -> list[dict]:
    original = original_root(manifest)
    identity = local_path(str(original / "evaluation/friedrich_code_v3/results/v3_2_formal_120_20260930_225036utc/run_identity_before.json"), manifest)
    frozen = json.loads(identity.read_text())
    require(frozen["cohort"]["roster_sha256"] == manifest["frozen_roster_sha256"], "roster hash differs")
    roster = frozen["roster"]
    require(len(roster) == 120 and len({(r["case_id"], r["candidate_id"]) for r in roster}) == 120,
            "not 120 distinct candidates")
    require(len({r["case_id"] for r in roster}) == 40, "not 40 distinct cases")
    for row in roster:
        graph = local_path(row["activity_graph_path"], manifest)
        require(graph.is_file() and sha(graph) == row["activity_graph_sha256"],
                f"candidate graph mismatch: {row['case_id']}/{row['candidate_id']}")
        # Candidate technical/manifests were historical v6 guard inputs, not
        # scoring inputs. Check them if present, but a clean branch needs only
        # the hash-verified graph plus the hash-verified frozen roster.
        for field, hash_field in (("candidate_manifest_path", "candidate_manifest_sha256"),
                                  ("technical_status_path", "technical_status_sha256")):
            target = local_path(row[field], manifest)
            if target.exists():
                require(target.is_file() and sha(target) == row[hash_field],
                        f"optional historical input changed: {row['case_id']}/{row['candidate_id']}/{field}")
        require(row["technical_status"] == "success", "candidate technical status differs")
    return roster


def verify_content(*, model_snapshot: Path | None = None, check_environment: bool = True) -> dict:
    manifest = checked_manifest()
    require(sha(FREEZE / "dependency_file_inventory.csv") == manifest["inventory_csv_sha256"],
            "dependency catalog mismatch")
    require(sha(FREEZE / "used_sibling_dirty_files.csv") == manifest["used_sibling_dirty_csv_sha256"],
            "sibling dirty-file catalog mismatch")
    catalog = list(csv.DictReader((FREEZE / "dependency_file_inventory.csv").open(newline="")))
    require(len(catalog) == manifest["file_count"] == len(manifest["files"]), "catalog count mismatch")
    indexed = {row["path"]: row for row in catalog}
    require(len(indexed) == len(catalog), "duplicate catalog paths")
    for item in manifest["files"]:
        row = indexed.get(item["path"])
        require(row is not None and row["sha256"] == item["sha256"] and
                row["scope"] == item["scope"] and set(row["roles"].split(";")) == set(item["roles"]),
                f"catalog/manifest conflict: {item['path']}")
    scope_path = FREEZE / "branch_file_scope.csv"
    require(sha(scope_path) == BRANCH_SCOPE_SHA256, "approved branch file scope changed")
    scope = list(csv.DictReader(scope_path.open(newline="")))
    original = original_root(manifest)
    frozen_local = {x["path"]: x for x in manifest["files"] if x["scope"] == "studio"}
    local_count = 0
    for row in scope:
        if row["bucket"] != "MUST_COMMIT":
            continue
        target = local_path(row["path"], manifest)
        require(target.is_file() and sha(target) == row["sha256"], f"required checkout file changed: {target}")
        if row["path"] in frozen_local:
            require(row["sha256"] == frozen_local[row["path"]]["sha256"], "scope/catalog hash conflict")
        local_count += 1
    require(local_count == 278, "required checkout scope count differs")
    archive_contents = verify_archive(manifest)
    roster = verify_roster(manifest)
    final = local_path(str(Path(manifest["validated_run"]) / "candidate_results.jsonl"), manifest)
    final_run = local_path(str(Path(manifest["validated_run"]) / "validation_manifest.json"), manifest)
    require(sha(final) == manifest["validated_result_sha256"], "frozen final result hash mismatch")
    require(sha(final_run) == manifest["validated_run_manifest_sha256"], "frozen final run manifest mismatch")
    result_rows = [json.loads(line) for line in final.open(encoding="utf-8")]
    require(len(result_rows) == 120 and
            [(r["case_id"], r["candidate_id"], r["graph_sha256"]) for r in result_rows] ==
            [(r["case_id"], r["candidate_id"], r["activity_graph_sha256"]) for r in roster],
            "frozen final results do not match the roster")
    model = verify_model(manifest, model_snapshot)
    env = verify_environment(manifest) if check_environment else {"status": "not_checked"}
    return {"status": "PASS", "mode": "content_verification", "candidate_count": len(roster),
            "case_count": 40, "required_checkout_files_verified": local_count,
            "archived_sibling_files_verified": len(archive_contents),
            "taxonomy_addendum_sha256": ADDENDUM_SHA256,
            "frozen_result_sha256": sha(final), "model": model, "environment": env,
            "scores_recomputed": False, "original_repository_root": str(original)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-snapshot", type=Path, help="pinned revision snapshot directory")
    parser.add_argument("--skip-environment-check", action="store_true",
                        help="verify content on another platform; replay still requires matching dependencies")
    args = parser.parse_args()
    print(json.dumps(verify_content(model_snapshot=args.model_snapshot,
                                    check_environment=not args.skip_environment_check), indent=2))


if __name__ == "__main__":
    main()
