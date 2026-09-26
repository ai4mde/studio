"""Read-only identity and provenance checks for the frozen V3 source corpus."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


DEFAULT_FROZEN_ROOT = Path(__file__).resolve().parent / "control_inventory/corpus_v1/v3_1/frozen"
DEFAULT_SOURCE_ROOT = (
    Path(__file__).resolve().parents[3]
    / "studio-semantic-v2/evaluation/friedrich_semantic_v2/inventories/corpus_v1/cases"
)
APPROVED_CORPUS_SHA256 = "5f9765bda2ea5d9d9f4a78603207bb0a2ed6532fd0c935149c275595c7d5be8a"


class FrozenCorpusError(ValueError):
    """Frozen data or a dependency has changed since researcher approval."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_verified(path: Path, expected: str) -> bytes:
    data = path.read_bytes()
    if _sha(data) != expected:
        raise FrozenCorpusError(f"SHA-256 mismatch: {path}")
    return data


@dataclass(frozen=True, slots=True)
class FrozenCase:
    case_id: str
    control: Mapping[str, Any]
    reviewed_action: Mapping[str, Any]
    source_text: str
    reference_evidence: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class FrozenCorpus:
    root: Path
    source_root: Path
    manifest: Mapping[str, Any]
    contract: Mapping[str, Any]

    @property
    def corpus_sha256(self) -> str:
        return str(self.manifest["corpus_sha256"])

    @property
    def case_ids(self) -> tuple[str, ...]:
        return tuple(self.manifest["components"]["cases"])

    def load_case(self, case_id: str) -> FrozenCase:
        try:
            component = self.manifest["components"]["cases"][case_id]
        except KeyError as exc:
            raise FrozenCorpusError(f"unsupported case: {case_id}") from exc
        control = json.loads(_read_verified(
            self.root / component["relative_path"], component["control_inventory_sha256"]
        ))
        source_dir = self.source_root / case_id
        source_bytes = _read_verified(source_dir / "process_text.txt", component["source_sha256"])
        action = json.loads(_read_verified(
            source_dir / "inventory_reviewed.json", component["reviewed_action_inventory_sha256"]
        ))
        reference = json.loads((source_dir / "reference_evidence.json").read_bytes())
        if (
            control["status"] != "FROZEN"
            or control["case_id"] != case_id
            or control["inventory_version"] != component["origin_inventory_version"]
            or (control["scoring_contract_version"] != self.contract["contract_version"]
                and component["origin_inventory_version"].startswith("v3.1"))
            or control["reviewed_action_inventory_sha256"] != component["reviewed_action_inventory_sha256"]
            or control["source_hash"] != component["source_sha256"]
            or reference["reference_sha256"] != component["reference_model_sha256"]
        ):
            raise FrozenCorpusError(f"frozen dependency identity mismatch: {case_id}")
        return FrozenCase(case_id, control, action, source_bytes.decode(control["source_encoding"]), reference)


def load_frozen_corpus(
    root: str | Path = DEFAULT_FROZEN_ROOT,
    source_root: str | Path = DEFAULT_SOURCE_ROOT,
    *,
    expected_sha256: str = APPROVED_CORPUS_SHA256,
) -> FrozenCorpus:
    root, source_root = Path(root), Path(source_root)
    manifest = json.loads((root / "freeze_manifest.json").read_bytes())
    if manifest.get("status") != "FROZEN" or manifest.get("corpus_sha256") != expected_sha256:
        raise FrozenCorpusError("V3 frozen corpus identity differs from the approved identity")
    components = manifest["components"]
    canonical = json.dumps(components, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    if _sha(canonical) != expected_sha256 or len(components["cases"]) != 40:
        raise FrozenCorpusError("V3 frozen corpus component digest or case count mismatch")
    contract_component = components["scoring_contract"]
    contract = json.loads(_read_verified(
        root / contract_component["relative_path"], contract_component["sha256"]
    ))
    if (contract.get("status") != "FROZEN"
        or contract.get("contract_version") != manifest.get("effective_scoring_contract_version")
        or contract.get("contract_version") != "v3.1-cfi-anchor-evidence-1"):
        raise FrozenCorpusError("V3 scoring contract is not frozen")
    amendment = components["amendment_history"]
    _read_verified(root / amendment["relative_path"], amendment["sha256"])
    for item in components["action_scoring_code"].values():
        _read_verified(Path(item["path"]), item["sha256"])
    corpus = FrozenCorpus(root, source_root, manifest, contract)
    # Verify every frozen file and external source dependency before a candidate is examined.
    for case_id in corpus.case_ids:
        corpus.load_case(case_id)
    return corpus
