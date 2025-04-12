from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse, HttpResponseNotAllowed

from workflow_engine.models import ActiveProcess, Process

def login_check(user):
    return user.is_authenticated

# Auth
def start_process(request, process_id) -> HttpResponse:
    if request.method == "POST":
        process = get_object_or_404(Process, id=process_id)
        process.start_process(request.user)
        # TODO implement URL
        return redirect('/manager')
    return HttpResponseNotAllowed(["POST"])


# Auth
def redirect_to_process(request, active_process_id) -> HttpResponse:
    if request.method == "POST":
        active_process = get_object_or_404(ActiveProcess, id=active_process_id)
        # TODO implement URL
        return redirect('/manager')
    return HttpResponseNotAllowed(["POST"])


# Auth
def complete_process_step(request, active_process_id) -> HttpResponse:
    if request.method == "POST":
        active_process = get_object_or_404(ActiveProcess, id=active_process_id)
        active_process.complete_node(request.user)
        return redirect('/manager')
    return HttpResponseNotAllowed(["POST"])