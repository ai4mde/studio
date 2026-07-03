from django.http import HttpRequest

from diagram.models import Diagram

def get_diagram(request: HttpRequest) -> Diagram | None:
    if not request.resolver_match:
        return None

    if not request.resolver_match.kwargs.get("diagram"):
        return None

    id = request.resolver_match.kwargs.get("diagram")
    return Diagram.objects.get(id=id)

