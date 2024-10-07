from ninja import ModelSchema
from chatlog.models import ChatLog


class ReadChatLog(ModelSchema):
    class Meta:
        model = ChatLog
        fields = ["id", "name", "chat", "path"]


class CreateChatLog(ModelSchema):
    class Meta:
        model = ChatLog
        fields = ["id", "name", "chat", "path"]


class UpdateChatLog(ModelSchema):
    class Meta:
        model = ChatLog
        fields = ["id", "name", "chat", "path"]


class DeleteChatLog(ModelSchema):
    class Meta:
        model = ChatLog
        fields = ["id"]


__all__ = ["ReadChatLog", "CreateChatLog", "UpdateChatLog", "DeleteChatLog"]
