from ninja import Router

llm_router = Router()


@llm_router.get("/healthz", auth=None, tags=["llm"])
def healthz(request):
    """Return a lightweight health check response."""
    return {"status": "ok", "service": "llm-django"}


__all__ = ["llm_router"]
