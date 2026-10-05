"""Replay the unchanged frozen v8 evaluator from a verified portable overlay."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import uuid

from verify_frozen_v8 import (ADDENDUM, FREEZE, REPO, checked_manifest,
                              local_path, require, sha, verify_archive,
                              verify_content, verify_roster)


DIMENSIONS = ("Action", "Flow", "Control Node", "Control Relation")


def aggregate_rows(rows: list[dict]) -> dict:
    """Mirror the descriptive aggregate in the frozen v6 runner, not scoring."""
    summary = {dimension: Counter() for dimension in DIMENSIONS}
    for row in rows:
        for dimension in DIMENSIONS:
            counts = row[dimension] if dimension == "Action" else row[dimension]["counts"]
            out = summary[dimension]
            for field in ("tp", "fp", "fn"):
                out[field] += counts[field]
            if dimension != "Action":
                out["indeterminate"] += counts["indeterminate_alignment_count"]
                out["required"] += counts["required_denominator"]
                out["na_candidates"] += int(counts.get("status") == "N/A")
                out["indeterminate_candidates"] += int(counts.get("status") == "indeterminate" or
                    (dimension != "Control Relation" and counts["f1"] is None))
            out["numeric_candidates"] += int(counts["f1"] is not None)
            out["null_candidates"] += int(counts["f1"] is None)
    result = {}
    for dimension, counts in summary.items():
        tp, fp, fn = (counts[name] for name in ("tp", "fp", "fn"))
        precision = tp / (tp + fp) if tp + fp else None
        recall = tp / (tp + fn) if tp + fn else None
        f1 = (2 * precision * recall / (precision + recall)
              if precision is not None and recall is not None and precision + recall
              else (0.0 if precision is not None and recall is not None else None))
        result[dimension] = dict(counts)
        result[dimension].update({
            "coverage": ((counts["required"] - counts["indeterminate"]) / counts["required"]
                         if counts["required"] else None) if dimension != "Action" else 1.0,
            "pooled_precision": precision, "pooled_recall": recall, "pooled_f1": f1,
        })
    return result


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def canonical_rows(rows: list[dict]) -> bytes:
    """Order-independent object encoding for comparison, including NaN diagnostics."""
    return ("\n".join(json.dumps(row, sort_keys=True, separators=(",", ":"),
                                  ensure_ascii=False) for row in rows) + "\n").encode()


def replay(model_snapshot: Path | None, output_root: Path | None) -> Path:
    verification = verify_content(model_snapshot=model_snapshot)
    manifest = checked_manifest()
    roster = verify_roster(manifest)
    sibling = verify_archive(manifest)
    snapshot = Path(verification["model"]["snapshot"])

    if output_root is None:
        output_root = REPO / "evaluation/friedrich_code_v3/results"
    output_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%futc")
    output = output_root / f"portable_v8_replay_{stamp}_{uuid.uuid4().hex[:8]}"
    output.mkdir(exist_ok=False)
    print(f"Verified content. Portable replay output: {output}", flush=True)

    with tempfile.TemporaryDirectory(prefix="code_v8_portable_") as temporary:
        overlay = Path(temporary)
        evaluation_dir = overlay / "studio-semantic-v2/evaluation"
        for relative, data in sibling.items():
            target = overlay / "studio-semantic-v2" / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        taxonomy = evaluation_dir / "friedrich_v3/compatibility_v3.json"
        shutil.copyfile(ADDENDUM, taxonomy)
        require(sha(taxonomy) == verification["taxonomy_addendum_sha256"], "taxonomy overlay mismatch")

        model_cache = overlay / "model_cache"
        model_link = model_cache / f"models--{manifest['model']['name'].replace('/', '--')}" / "snapshots" / manifest["model"]["revision"]
        model_link.parent.mkdir(parents=True, exist_ok=True)
        model_link.symlink_to(snapshot, target_is_directory=True)

        sys.path.insert(0, str(REPO))
        import evaluation
        evaluation.__path__.insert(0, str(evaluation_dir))
        from evaluation.friedrich_v3.action import (ACTION_MODEL_NAME, ACTION_MODEL_REVISION,
                                                  SentenceTransformerSimilarity)
        from evaluation.friedrich_v3.adapters import load_generated_graph
        from evaluation.friedrich_code_v3.combined_candidate_v3 import SourceEligibilityCorpus
        from evaluation.friedrich_code_v3.combined_candidate_v8 import (VERSION,
            evaluate_combined_candidate_v8)
        from evaluation.friedrich_code_v3.inventory import FrozenCorpus

        require(VERSION == manifest["evaluator_version"], "loaded evaluator version differs")
        require(ACTION_MODEL_NAME == manifest["model"]["name"] and
                ACTION_MODEL_REVISION == manifest["model"]["revision"], "model binding differs")
        require(Path(sys.modules["evaluation.friedrich_v3.action"].__file__).is_relative_to(evaluation_dir),
                "loaded sibling Action module outside portable overlay")
        require(Path(sys.modules["evaluation.friedrich_semantic_v2.evaluator_adapter"].__file__).is_relative_to(evaluation_dir),
                "loaded sibling adapter outside portable overlay")

        frozen_root = REPO / "evaluation/friedrich_code_v3/control_inventory/corpus_v1/v3_1/frozen"
        control_manifest = json.loads((frozen_root / "freeze_manifest.json").read_text())
        control_contract = json.loads((frozen_root / "scoring_contract.json").read_text())
        source_root = evaluation_dir / "friedrich_semantic_v2/inventories/corpus_v1/cases"
        corpus = SourceEligibilityCorpus(FrozenCorpus(frozen_root, source_root,
                                                      control_manifest, control_contract))
        require(tuple(corpus.case_ids) == tuple(sorted({r["case_id"] for r in roster},
                                                  key=lambda s: tuple(map(int, s.split("-"))))) or
                set(corpus.case_ids) == {r["case_id"] for r in roster}, "corpus/roster cases differ")
        model = SentenceTransformerSimilarity(ACTION_MODEL_NAME, ACTION_MODEL_REVISION, str(model_cache))
        results: list[dict] = []
        path = output / "candidate_results.jsonl"
        with path.open("w", encoding="utf-8") as stream:
            for index, slot in enumerate(roster, 1):
                graph_path = local_path(slot["activity_graph_path"], manifest)
                require(sha(graph_path) == slot["activity_graph_sha256"], "graph changed during replay")
                graph = load_generated_graph(graph_path)
                row = evaluate_combined_candidate_v8(slot["case_id"], slot["candidate_id"], graph,
                                                     model, corpus=corpus).to_dict()
                row["configuration_version"] = VERSION
                row["graph_sha256"] = slot["activity_graph_sha256"]
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                results.append(row)
                if index % 10 == 0:
                    print(f"Replayed {index}/120 candidates", flush=True)
        for name, module in tuple(sys.modules.items()):
            if name.startswith(("evaluation.friedrich_v3", "evaluation.friedrich_semantic_v2",
                                "evaluation.friedrich_semantic")) and getattr(module, "__file__", None):
                require(Path(module.__file__).is_relative_to(evaluation_dir),
                        f"runtime loaded a mutable sibling module: {name}")

    frozen_path = local_path(str(Path(manifest["validated_run"]) / "candidate_results.jsonl"), manifest)
    frozen_rows = [json.loads(line) for line in frozen_path.open(encoding="utf-8")]
    differing = [{"case_id": new["case_id"], "candidate_id": new["candidate_id"]}
                 for new, old in zip(results, frozen_rows, strict=True)
                 if canonical_rows([new]) != canonical_rows([old])]
    raw_differing = [{"case_id": json.loads(new)["case_id"],
                      "candidate_id": json.loads(new)["candidate_id"]}
                     for new, old in zip(path.read_text().splitlines(),
                                         frozen_path.read_text().splitlines(), strict=True)
                     if new != old]
    frozen_summary = json.loads(local_path(str(Path(manifest["validated_run"]) /
        "aggregate_summary.json"), manifest).read_text())["dimensions"]
    replay_summary = aggregate_rows(results)
    result_hash_matches = sha(path) == manifest["validated_result_sha256"]
    canonical_replay_sha = hashlib.sha256(canonical_rows(results)).hexdigest()
    canonical_frozen_sha = hashlib.sha256(canonical_rows(frozen_rows)).hexdigest()
    canonical_match = canonical_replay_sha == canonical_frozen_sha
    metrics_match = replay_summary == frozen_summary
    write_json(output / "aggregate_summary.json", {"dimensions": replay_summary})
    comparison = {"status": "BYTE_EXACT_MATCH" if result_hash_matches and metrics_match else
                  ("SEMANTIC_MATCH_BYTE_ORDER_DIFFERS" if canonical_match and metrics_match else "DIFFERENT"),
                  "frozen_result_sha256": manifest["validated_result_sha256"],
                  "replayed_result_sha256": sha(path),
                  "byte_exact_result_match": result_hash_matches,
                  "canonical_frozen_sha256": canonical_frozen_sha,
                  "canonical_replayed_sha256": canonical_replay_sha,
                  "canonical_object_match": canonical_match,
                  "raw_differing_candidate_count": len(raw_differing),
                  "raw_differing_candidates": raw_differing,
                  "candidate_object_differences": differing,
                  "aggregate_metrics_match": metrics_match,
                  "candidate_count": len(results)}
    write_json(output / "replay_comparison.json", comparison)
    write_json(output / "replay_manifest.json", {
        "mode": "portable_execution_replay", "evaluator_version": manifest["evaluator_version"],
        "freeze_manifest_sha256": sha(FREEZE / "final_code_v8_freeze_manifest.json"),
        "verifier_sha256": sha(Path(__file__).with_name("verify_frozen_v8.py")),
        "replay_wrapper_sha256": sha(Path(__file__)),
        "dependency_map_sha256": sha(Path(__file__).with_name("replay_dependency_map.csv")),
        "taxonomy_addendum_sha256": verification["taxonomy_addendum_sha256"],
        "archive_sha256": manifest["sibling_archive"]["sha256"],
        "model_revision": manifest["model"]["revision"],
        "model_tree_sha256": manifest["model"]["tree_sha256"],
        "roster_sha256": manifest["frozen_roster_sha256"],
        "verified_candidate_count": len(roster), "api_calls": 0,
        "scoring_module_modified": False, "result": comparison,
    })
    print(json.dumps(comparison, indent=2), flush=True)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-snapshot", type=Path, help="pinned revision snapshot directory")
    parser.add_argument("--output-root", type=Path, help="directory for a new replay results folder")
    args = parser.parse_args()
    replay(args.model_snapshot, args.output_root)


if __name__ == "__main__":
    main()
