import uuid
from django.db import models
from django.contrib.auth import get_user_model


class UserEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        get_user_model(), on_delete=models.SET_NULL, null=True, blank=True
    )
    session_id = models.CharField(max_length=64, db_index=True)
    event_type = models.CharField(max_length=64, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.session_id} | {self.event_type} | {self.timestamp:%Y-%m-%d %H:%M:%S}"
