from typing import List

from pydantic import BaseModel

from ai_runtime.chains import ChainRunner, ChainStep
from ai_runtime.routing import call_model


class TasteProfile(BaseModel):
    genres: List[str]
    notes: str = ""


class Recommendation(BaseModel):
    books: List[str]


class ReadingPlan(BaseModel):
    ordered: List[str]
    summary: str


STEPS = [
    ChainStep(name="analyze_taste", prompt_name="reading_plan_analyze_taste_v1",
              output_schema=TasteProfile, output_key="taste"),
    ChainStep(name="recommend", prompt_name="reading_plan_recommend_v1",
              output_schema=Recommendation, output_key="recommendation"),
    ChainStep(name="sequence", prompt_name="reading_plan_sequence_v1",
              output_schema=ReadingPlan, output_key="plan"),
]


def _build_taste_context(instance):
    # M02: the member's borrowed-book history from the generated ORM.
    from shared_models.models import Loan, BookLoan
    borrowed = []
    for loan in Loan.objects.filter(Customer=instance):
        for bl in BookLoan.objects.filter(Loan=loan):
            book = bl.Book
            if book is not None:
                borrowed.append({"title": getattr(book, "title", "") or "",
                                 "category": getattr(book, "category", "") or "",
                                 "author": getattr(getattr(book, "Author", None), "name", "") or ""})
    return {"borrowed_books": borrowed}


def run_reading_plan(ai_config, instance):
    """M04 chain orchestration for Customer.reading_plan. Returns (summary<=255, ChainResult, mode)
    for write-back + logging. Routes via the strong profile (M06)."""
    model_profile = ai_config.get("model_profile", "strong")
    modes = []

    def llm_caller(prompt):
        routed = call_model(model_profile, prompt)
        modes.append(routed["mode"])
        return routed["content"]

    context = _build_taste_context(instance)
    result = ChainRunner(STEPS, llm_caller).run(context)
    summary = None
    if result.success and "plan" in result.outputs:
        summary = result.outputs["plan"].summary[:255]
    mode = modes[0] if modes else None
    return summary, result, mode