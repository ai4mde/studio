import json
from pathlib import Path
import uuid
from model.llm.baseline_generator import generate_activity_model
from model.llm.converter import convert_to_ai4mde
from model.llm.refinement_generator import refine_activity_model


def main() -> None:
    process_text = """
    A customer places an order on an e-commerce website.
    The system checks inventory, validates payment, and either confirms or rejects the order.
    If confirmed, the warehouse prepares the shipment and a confirmation email is sent.
    """

    # 1) Generate baseline clean graph
    clean_model = generate_activity_model(process_text)

    # 2) Convert to AI4MDE JSON (initial model)
    initial_model = convert_to_ai4mde(
        clean_model,
        system_id=str(uuid.uuid4()),
        diagram_id=str(uuid.uuid4()),
        name="Generated Activity Diagram",
        description="Baseline AI4MDE output",
    )

    # 3) Refine the AI4MDE model
    refinement_instruction = (
        "Add a separate step to send a confirmation email after confirming the order, "
        "before the process ends."
    )

    refined_model = refine_activity_model(
        process_text=process_text,
        current_model=initial_model,
        refinement_instruction=refinement_instruction,
    )

    # 4) Save both initial and refined AI4MDE JSONs
    Path("initial_activity_model.json").write_text(
        json.dumps(initial_model, indent=2), encoding="utf-8"
    )
    Path("refined_activity_model.json").write_text(
        json.dumps(refined_model, indent=2), encoding="utf-8"
    )

    print("Wrote initial_activity_model.json and refined_activity_model.json")


if __name__ == "__main__":
    main()
