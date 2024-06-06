from ninja import Router

from .views import prompt

prompt_router = Router()
prompt_router.add_router("", prompt, tags=["prompt"])


__all__ = ["prompt_router"]
