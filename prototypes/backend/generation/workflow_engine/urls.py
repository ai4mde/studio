from django.urls import path
from workflow_engine import views

app_name = "workflow_engine"
urlpatterns = [
    path("start_process/<int:process_id>/", views.StartProcessView.as_view(), name="start_process"),
    path("redirect_to_process/<int:active_process_node_id>/", views.RedirectToProcessView.as_view(), name="redirect_to_process"),
    path("delete_process/<int:active_process_node_id>/", views.DeleteProcessView.as_view(), name="delete_process"),
    path("complete_process_step/<int:active_process_node_id>/", views.CompleteProcessStepView.as_view(), name="complete_process_step"),
    path("change_user_assignment/<int:pk>/<str:app>", views.ChangeUserAssignmentUpdateView.as_view(), name="change_user_assignment"),
]