import json
from pathlib import Path
import uuid

from model.llm.baseline_generator import generate_activity_model, export_activity_model
from model.llm.converter import convert_to_ai4mde


def main() -> None:
    process_text = """
    A customer places an order on the website, payment is validated,
    and the order is either confirmed or rejected.
    If confirmed, the warehouse prepares the shipment and sends a confirmation email.
    """

    # 1) Baseline: clean activity diagram
    clean_model = generate_activity_model(process_text)
    print("=== CLEAN MODEL ===")
    print(json.dumps(clean_model, indent=2))

    # Also save the clean model explicitly (optional)
    Path("clean_activity_model.json").write_text(
        json.dumps(clean_model, indent=2), encoding="utf-8"
    )

    system_id = str(uuid.uuid4())
    diagram_id = str(uuid.uuid4())
    # 2) Convert clean diagram → AI4MDE JSON
    ai4mde_model = convert_to_ai4mde(
        clean_model,
        system_id=system_id,
        diagram_id=diagram_id,
        name="Generated Activity Diagram",
        description="Generated from baseline LLM",
    )

    print("\n=== AI4MDE MODEL (summary) ===")
    print("Top-level keys:", list(ai4mde_model.keys()))
    print("Number of diagrams:", len(ai4mde_model.get("diagrams", [])))

    # 3) Save AI4MDE JSON to file for import into AI4MDE
    # writes activity_model.json in current dir
    export_activity_model(ai4mde_model)


if __name__ == "__main__":
    main()
