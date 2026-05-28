from django.contrib import admin
from .models import UserEvent


@admin.register(UserEvent)
class UserEventAdmin(admin.ModelAdmin):
    list_display = ["session_id", "user", "event_type", "timestamp"]
    list_filter = ["event_type", "timestamp"]
    search_fields = ["session_id", "user__username", "event_type"]
    readonly_fields = ["id", "timestamp", "metadata"]
    ordering = ["-timestamp"]
