from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TemplateEntry:
    prompt_name: str
    filename: str


TEMPLATE_DIR = Path(__file__).resolve().parent / "prompt_templates"

TEMPLATE_REGISTRY = {
    "DIAGRAM_GENERATE_ATTRIBUTE": TemplateEntry(
        prompt_name="DIAGRAM_GENERATE_ATTRIBUTE",
        filename="diagram_generate_attribute.j2",
    ),
    "DIAGRAM_GENERATE_METHOD": TemplateEntry(
        prompt_name="DIAGRAM_GENERATE_METHOD",
        filename="diagram_generate_method.j2",
    ),
    "DIAGRAM_GENERATE_ATTRIBUTE_RAG": TemplateEntry(
        prompt_name="DIAGRAM_GENERATE_ATTRIBUTE_RAG",
        filename="diagram_generate_attribute_rag.j2",
    ),
    "DIAGRAM_GENERATE_METHOD_RAG": TemplateEntry(
        prompt_name="DIAGRAM_GENERATE_METHOD_RAG",
        filename="diagram_generate_method_rag.j2",
    ),
    "PROSE_GENERATE_METADATA": TemplateEntry(
        prompt_name="PROSE_GENERATE_METADATA",
        filename="prose_generate_metadata.j2",
    ),
    "PROSE_STEP1_EXTRACT_ENTITIES": TemplateEntry(
        prompt_name="PROSE_STEP1_EXTRACT_ENTITIES",
        filename="prose_step1_extract_entities.j2",
    ),
    "PROSE_STEP2_INFER_RELATIONS": TemplateEntry(
        prompt_name="PROSE_STEP2_INFER_RELATIONS",
        filename="prose_step2_infer_relations.j2",
    ),
    "PROSE_STEP3_VALIDATE": TemplateEntry(
        prompt_name="PROSE_STEP3_VALIDATE",
        filename="prose_step3_validate.j2",
    ),
}


def get_template_entry(prompt_name: str) -> TemplateEntry:
    entry = TEMPLATE_REGISTRY.get(prompt_name)
    if entry is None:
        available = ", ".join(sorted(TEMPLATE_REGISTRY.keys()))
        raise ValueError(f"Invalid prompt name: {prompt_name}. Available: {available}")
    return entry


def get_template_path(prompt_name: str) -> Path:
    entry = get_template_entry(prompt_name)
    path = TEMPLATE_DIR / entry.filename
    if not path.exists():
        raise FileNotFoundError(f"Template file not found: {path}")
    return path
