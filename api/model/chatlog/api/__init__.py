from ninja import Router

from .views import chatlogs

chatlog_router = Router()
chatlog_router.add_router("chatlogs", chatlogs, tags=["chat log"])


__all__ = ["chatlog_router"]