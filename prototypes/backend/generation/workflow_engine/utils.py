from shared_models.models import User
from workflow_engine.models import ActionNode

def get_user_for_task(node: ActionNode) -> User | None:
    users = User.objects.filter(roles__contains=node.actor)
    # TODO: Implement a better distribution algorithm
    # For now, just return the first user that matches the actor
    return users.first() if users.exists() else None
