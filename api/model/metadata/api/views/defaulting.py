from metadata.models import System, Classifier, Interface
from metadata.api.schemas import ReadInterface

def create_default_interface(system: System, actor: Classifier) -> ReadInterface:
    return Interface.objects.create(
        name = actor.data['name'],
        description = actor.data['name'] + " application",
        system = system,
        actor = actor,
        data = "" # TODO: smart defaulting result goes here
    )