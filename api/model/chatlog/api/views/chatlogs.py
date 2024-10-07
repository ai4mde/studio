from typing import List

from chatlog.api.schemas import CreateChatLog, ReadChatLog, UpdateChatLog
from chatlog.models import ChatLog
from ninja import Router

chatlogs = Router()


@chatlogs.get("/", response=List[ReadChatLog])
def list_chatlogs(request):
    qs = ChatLog.objects.all()
    return qs


@chatlogs.get("/{uuid:chatlog_id}", response=ReadChatLog)
def read_chatlog(request, chatlog_id):
    return ChatLog.objects.get(id=chatlog_id)


@chatlogs.post("/", response=ReadChatLog)
def create_chatlog(request, chatlog: CreateChatLog):
    return ChatLog.objects.create(
        name=chatlog.name,
        chat=chatlog.chat,
        path=chatlog.path,
    )


@chatlogs.put("/{uuid:chatlog_id}", response=ReadChatLog)
def update_chatlog(request, chatlog_id, payload: UpdateChatLog):
    print(chatlog_id)
    print(payload)
    return None


@chatlogs.delete("/{uuid:chatlog_id}")
def delete_chatlog(request, chatlog_id):
    try:
        chatlog = ChatLog.objects.get(id=chatlog_id)
        chatlog.delete()
    except Exception as e:
        raise Exception("Failed to delete Chat log, error: " + e)
    return True
    

__all__ = ["chatlogs"]
