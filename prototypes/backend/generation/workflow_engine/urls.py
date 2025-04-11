from django.urls import path
from workflow_engine import views

app_name = "workflow_engine"
urlpatterns = [
    path("start_process/<int:process_id>/", views.start_process, name="start_process"),
]