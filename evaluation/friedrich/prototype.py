from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .adapters import activity_graph_to_eval_graph, friedrich_reference_to_eval_graph


def _extract_activity_graph(artifact: dict[str, Any]) -> dict[str, Any]:
    if "nodes" in artifact and "edges" in artifact:
        return artifact
    try:
        return artifact["api_payload"]["systems"][0]["activity_graph"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("Could not locate ActivityGraph in generated artifact") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Build two EvalGraphs for one case")
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--generated", required=True, type=Path)
    args = parser.parse_args()

    generated_artifact = json.loads(args.generated.read_text(encoding="utf-8"))
    result = {
        "reference": friedrich_reference_to_eval_graph(args.reference).to_dict(),
        "generated": activity_graph_to_eval_graph(
            _extract_activity_graph(generated_artifact)
        ).to_dict(),
    }
    print(json.dumps(result, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
