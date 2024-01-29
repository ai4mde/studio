from django.http import HttpRequest
from diagram.models import Diagram
from .node import create_node
from .edge import create_edge


def get_diagram(request: HttpRequest) -> Diagram | None:
    if not request.resolver_match:
        return None

    if not request.resolver_match.kwargs.get("diagram"):
        return None

    id = request.resolver_match.kwargs.get("diagram")
    return Diagram.objects.get(id=id)


__all__ = [
    "get_diagram",
    "create_node",
    "create_edge",
]
