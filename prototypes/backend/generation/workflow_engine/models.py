import re

from django.db import models
from django.utils.timezone import now
from django.db.models.query import QuerySet
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import PermissionDenied

from shared_models.models import User

# Imports


class ActionNode(models.Model):
    id = models.AutoField(primary_key=True)
    actor = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    process = models.ForeignKey("Process", related_name="action_nodes", on_delete=models.CASCADE)
    next_node_rule = models.OneToOneField("Rule", related_name="action_node", on_delete=models.PROTECT)

    def __str__(self):
        return self.name


class Process(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    start_node = models.ForeignKey(ActionNode, related_name="start_process", on_delete=models.PROTECT, null=True)

    action_nodes: QuerySet[ActionNode]

    @staticmethod
    def get_available_processes(user: User) -> QuerySet["Process"]:
        return Process.objects.filter(
            start_node__actor__in=user.roles,
        )

    def start_process(self, user: User) -> None:
        """Start a process for the given user."""
        assert self.start_node # TODO make start node required. This involves changing the workflow population migration.
        if self.start_node.actor not in user.roles:
            raise PermissionDenied(f"User {user.username} does not have the required role to start this process.")

        active_process = ActiveProcess.objects.create(
            process=self,
            active_node=self.start_node,
            user=user,
        )

        # Log the start of the process
        ActionLog.objects.create(
            status="ASSIGNED",
            process=self,
            action_node=self.start_node,
            active_process=active_process,
            user=user,
        )

    def __str__(self):
        return self.name


class Rule(models.Model):
    id = models.AutoField(primary_key=True)
    condition = models.JSONField(default=dict)

    action_node: ActionNode

    def evaluate_rule(self) -> ActionNode | None:
        # TODO this currently only works for case study 1 and has to be adapted in the future
        next_condition = self.condition.get("*")
        if next_condition == "END":
            return None
        if next_condition:
            match = re.match(r"NEXT\((\d+)\)", next_condition)
            if match:
                try:
                    return ActionNode.objects.get(id=int(match.group(1)))
                except ActionNode.DoesNotExist:
                    raise ValueError(f"Rule {self.id} references a non-existing action node: {match.group(1)}")
        raise ValueError(f"Rule {self.id} does not have a valid condition: {self.condition}")

    def __str__(self):
        return f"Next node rule for {self.action_node}"

class ActiveProcess(models.Model):
    id = models.AutoField(primary_key=True)
    completed = models.BooleanField(default=False)
    process = models.ForeignKey(Process, related_name="active_processes", on_delete=models.CASCADE)
    active_node = models.ForeignKey(ActionNode, related_name="active_processes", on_delete=models.PROTECT)
    user = models.ForeignKey(User, related_name="active_processes", on_delete=models.PROTECT)

    associated_model_instances: "QuerySet[AssociatedModelInstance]"

    # Properties

    def complete_node(self, user: User) -> None:
        """Complete the current node and progress to the next node if needed."""
        if self.completed:
            raise ValueError("This process is already completed.")
        
        if self.active_node.actor not in user.roles:
            raise PermissionDenied(f"User {user.username} does not have the required role to complete this step.")

        # Evaluate the rule to determine the next node
        next_node = self.active_node.next_node_rule.evaluate_rule()

        if not next_node:
            self._complete_process(user)
            return
        self._progress_to_next_node(next_node, user)
        

    def _complete_process(self, user: User) -> None:
        """Mark the process as completed and log the completion."""
        self.completed = True
        self.save()
        # Log the completion of the process
        current_action_log = ActionLog.objects.get(
            action_node=self.active_node,
            active_process=self,
        )
        current_action_log.completed_at = now()
        current_action_log.status = "COMPLETED"
        current_action_log.save()

    def _progress_to_next_node(self, next_node: ActionNode, user: User) -> None:
        """Progress to the next node and assign the next user."""

        # Log the completion of the current node
        current_action_log = ActionLog.objects.get(
            action_node=self.active_node,
            active_process=self,
        )
        current_action_log.completed_at = now()
        current_action_log.status = "COMPLETED"
        current_action_log.save()

        # Set the next node as the active node
        self.active_node = next_node

        # Determine the next user for the task
        next_user = self._get_next_user(next_node, user)
        self.user = next_user
        self.save()

        # Log the assignment of the next node
        ActionLog.objects.create(
            status="ASSIGNED",
            process=self.process,
            action_node=next_node,
            active_process=self,
            user=user,
        )

    def _get_next_user(self, next_node: ActionNode, current_user: User) -> User:
        """Determine the next user for the given node."""
        # Try to keep the current user for the next node
        if next_node.actor in current_user.roles:
            return current_user

        users = User.objects.filter(roles__contains=next_node.actor)
        # TODO: Implement a better distribution algorithm
        # For now, just return the first user that matches the actor
        next_user = users.first() if users.exists() else None
        if not next_user:
            raise ValueError(f"No user found for task {next_node}")
        return next_user
    
    def __str__(self):
        return f"Active process for {self.process}"

class AssociatedModelInstance(models.Model):
    id = models.AutoField(primary_key=True)
    instance_id = models.IntegerField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    instance = GenericForeignKey('content_type', 'instance_id')
    active_process = models.ForeignKey(ActiveProcess, related_name="associated_model_instances", on_delete=models.PROTECT)

    def __str__(self):
        return f"Instance {self.instance_id} of {self.content_type.name}"


class ActionLog(models.Model):
    STATUS_CHOICES = [
        ("STARTED", "Started"),
        ("COMPLETED", "Completed"),
        ("ASSIGNED", "Assigned"),
    ]


    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    process = models.ForeignKey(Process, related_name="process_action_logs", on_delete=models.CASCADE)
    action_node = models.ForeignKey(ActionNode, related_name="action_logs", on_delete=models.CASCADE)
    active_process = models.ForeignKey(ActiveProcess, related_name="active_process_action_logs", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="action_logs", on_delete=models.CASCADE)

    def __str__(self):
        return f"Action log for {self.process} - {self.status} at {self.created_at}"