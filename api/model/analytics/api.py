import csv
from datetime import datetime
from django.http import HttpResponse
from ninja import Router, Schema
from model.auth import user_from_token
from .models import UserEvent

analytics_router = Router()


class EventSchema(Schema):
    session_id: str
    event_type: str
    metadata: dict = {}


@analytics_router.post("/event", auth=None)
def track_event(request, payload: EventSchema):
    user = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        user = user_from_token(auth_header[7:])
    UserEvent.objects.create(
        user=user,
        session_id=payload.session_id,
        event_type=payload.event_type,
        metadata=payload.metadata,
    )
    return {"ok": True}


@analytics_router.get("/export.csv")
def export_csv(request):
    events = UserEvent.objects.select_related("user").all()
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="events_{datetime.now():%Y%m%d}.csv"'
    writer = csv.writer(response)
    writer.writerow(["session_id", "user_id", "username", "event_type", "timestamp", "metadata"])
    for e in events:
        writer.writerow([
            e.session_id,
            str(e.user.id) if e.user else "",
            e.user.username if e.user else "anonymous",
            e.event_type,
            e.timestamp.isoformat(),
            e.metadata,
        ])
    return response
