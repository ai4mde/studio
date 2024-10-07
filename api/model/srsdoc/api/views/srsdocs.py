from typing import List

from srsdoc.api.schemas import CreateSRSDocument, ReadSRSDocument, UpdateSRSDocument
from srsdoc.models import SRSDocument
from ninja import Router

srsdocs = Router()


@srsdocs.get("/", response=List[ReadSRSDocument])
def list_srsdocs(request):
    qs = SRSDocument.objects.all()
    return qs


@srsdocs.get("/{uuid:srsdoc_id}", response=ReadSRSDocument)
def read_srsdoc(request, srsdoc_id):
    return SRSDocument.objects.get(id=srsdoc_id)


@srsdocs.post("/", response=ReadSRSDocument)
def create_srsdoc(request, srsdoc: CreateSRSDocument):
    return SRSDocument.objects.create(
        title=srsdoc.title,
        version=srsdoc.version,
        description=srsdoc.description,
        path=srsdoc.path,
    )


@srsdocs.put("/{uuid:srsdoc_id}", response=ReadSRSDocument)
def update_srsdoc(request, srsdoc_id, payload: UpdateSRSDocument):
    print(srsdoc_id)
    print(payload)
    return None


@srsdocs.delete("/{uuid:srsdoc_id}")
def delete_srsdoc(request, srsdoc_id):
    try:
        srsdoc = SRSDocument.objects.get(id=srsdoc_id)
        srsdoc.delete()
    except Exception as e:
        raise Exception("Failed to delete Software Requirements Specification document, error: " + e)
    return True
    

__all__ = ["srsdocs"]
