from ninja import Router

from metadata.api.schemas import NewClassifierInput

meta = Router()


@meta.get("/")
def get_meta(request):
    return ""


@meta.get("/classifiers/")
def get_classifiers(request):
    return ""


@meta.post("/classifiers/")
def create_classifiers(request, data: NewClassifierInput):
    return ""


__all__ = [
    "meta",
]
