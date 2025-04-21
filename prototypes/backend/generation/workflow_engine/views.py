from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse, HttpResponseNotAllowed

from workflow_engine.models import ActionLog, ActiveProcess, Process

def login_check(user):
    return user.is_authenticated

# Auth
def start_process(request, process_id) -> HttpResponse:
    if request.method == "POST":
        process = get_object_or_404(Process, id=process_id)
        active_process = process.start_process(request.user)
        return redirect(f"{active_process.active_node.url}/{active_process.id}/{active_process.active_node.id}")
    return HttpResponseNotAllowed(["POST"])


# Auth
def redirect_to_process(request, active_process_id) -> HttpResponse:
    if request.method == "POST":
        active_process = get_object_or_404(ActiveProcess, id=active_process_id)
        return redirect(f"{active_process.active_node.url}/{active_process.id}/{active_process.active_node.id}")
    return HttpResponseNotAllowed(["POST"])


# Auth
def complete_process_step(request, active_process_id) -> HttpResponse:
    if request.method == "POST":
        active_process = get_object_or_404(ActiveProcess, id=active_process_id)
        active_process.complete_node(request.user)
        return redirect(f'/{request.user.roles[0]}')
    return HttpResponseNotAllowed(["POST"])


# Auth
def action_log_view(request, template_name) -> HttpResponse:
    action_logs = ActionLog.objects.all()

    status_filter = request.GET.get("status")
    if status_filter:
        action_logs = action_logs.filter(status=status_filter)

    user_filter = request.GET.get("user")
    if user_filter:
        action_logs = action_logs.filter(user__username=user_filter)
    
    active_process_filter = request.GET.get("active_process_id")
    if active_process_filter:
        action_logs = action_logs.filter(active_process__id=active_process_filter)

    context = {
        'action_logs': action_logs,
        'status_choices': ActionLog.STATUS_CHOICES,
    }
    return render(request, template_name, context)
