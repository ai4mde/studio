from django.urls import path
from workflow_engine import views

app_name = "workflow_engine"
urlpatterns = [
    path("start_process/<int:process_id>/", views.start_process, name="start_process"),
    path("redirect_to_process/<int:active_process_id>/", views.redirect_to_process, name="redirect_to_process"),
    path("complete_process_step/<int:active_process_id>/", views.complete_process_step, name="complete_process_step"),
]