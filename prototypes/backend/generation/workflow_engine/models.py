import importlib
import json
import logging
from operator import eq, ne, lt, le, gt, ge
from typing import NamedTuple, Union

from django.db import models
from django.utils.timezone import now
from django.db.models.query import QuerySet
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.exceptions import PermissionDenied, ValidationError

from shared_models.models import User

# Imports


logger = logging.getLogger(__name__)

class Condition(NamedTuple):
    """
        Named tuple to represent a condition in the workflow.
    """
    operator: str
    threshold: int
    aggregator: str | None
    target_attribute: str
    target_class_name: str
    target_attribute_type: str


class NextNode(NamedTuple):
    """
        Named tuple to represent the next node in the workflow.
    """
    next: Union[int, str, list["NextNode"]]
    condition: Condition | None = None


class ConditionField(models.JSONField):
    """
        Custom field to handle the condition field to determine the next node. 
    """

    def from_db_value(self, value, expression, connection) -> list[NextNode] | None:
        """Validate JSON string from the database and convert into a structured Python object."""
        if value is None:
            return value
        raw_data = json.loads(value)
        return self._to_structured_format(raw_data)

    def _to_structured_format(self, raw_data: list) -> list[NextNode]:
        """
            Convert the raw data into a structured format.
        """
        return [
            NextNode(
                next=item['next'] if not isinstance(item['next'], list) else self._to_structured_format(item['next']),
                condition=Condition(**{key: item['condition'][key] for key in Condition._fields}) if 'condition' in item else None
            ) for item in raw_data
        ]


class ActionNode(models.Model):
    id = models.AutoField(primary_key=True)
    actor = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    url = models.CharField(max_length=255, null=True, blank=True)
    custom_code = models.CharField(max_length=255, null=True, blank=True)
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

    def start_process(self, user: User) -> "ActiveProcess":
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
            status="STARTED_PROCESS",
            action_node=self.start_node,
            active_process=active_process,
            user=user,
        )
        return active_process

    def __str__(self):
        return self.name


class Rule(models.Model):
    id = models.AutoField(primary_key=True)
    next = models.CharField(max_length=5, null=True, blank=True)
    condition = ConditionField(default=list, null=True, blank=True)

    action_node: ActionNode

    type_converters = {
        "int": int,
        "str": str,
        "bool": lambda x: x.lower() == "true",
    }
    operators = {
        "==": eq,
        "!=": ne,
        "<": lt,
        "<=": le,
        ">": gt,
        ">=": ge,
    }

    def _get_action_node(self, node_id: int) -> ActionNode:
        try:
            return ActionNode.objects.get(id=node_id)
        except ActionNode.DoesNotExist:
            raise ValueError(f"Rule {self.id} references a non-existing action node: {node_id}")

    def _evaluate_condition(self, active_process: "ActiveProcess", condition: Condition) -> bool:
        target_property_name = f"{condition.target_class_name.lower()}s"
        target_objects = getattr(active_process, target_property_name, None)

        if target_objects is None or not isinstance(target_objects, QuerySet):
            raise ValueError(f"Active process {active_process.id} does not have a QuerySet property named {target_property_name}")
                
        if condition.aggregator:
            if condition.aggregator == "sum":
                value = target_objects.aggregate(total=models.Sum(condition.target_attribute))["total"]
            elif condition.aggregator == "avg":
                value = target_objects.aggregate(avg=models.Avg(condition.target_attribute))["avg"]
            elif condition.aggregator == "max":
                value = target_objects.aggregate(max=models.Max(condition.target_attribute))["max"]
            elif condition.aggregator == "min":
                value = target_objects.aggregate(min=models.Min(condition.target_attribute))["min"]
            elif condition.aggregator == "count":
                value = target_objects.count()
            else:
                raise ValueError(f"Unsupported aggregator: {condition.aggregator}")

            # Return False if the aggregator fails to return a value
            if value is None:
                return False
        else:
            # If no aggregator is specified, we assume the condition is a direct comparison with a single objects
            if len(target_objects) > 1:
                logger.warning(
                    f"Condition {condition} is not an aggregator but a direct comparison. The target object is a list of length {len(target_objects)}."
                    "This should be a single object. Taking the first object for comparison. Please check the workflow configuration."
                )
            first_object = target_objects.first()
            if not first_object:
                logger.warning(
                    f"Condition {condition} is not an aggregator but a direct comparison. The target object is empty."
                    "This should be a single object. Please check the workflow configuration."
                )
                return False
            value = getattr(first_object, condition.target_attribute, None)
            
        # Convert the threshold to the correct type
        try:
            # Count does not have a target attribute and thus no type. Count is always compared to an int.
            threshold = (
                self.type_converters[condition.target_attribute_type](condition.threshold)
                if condition.aggregator != "count"
                else int(condition.threshold)
            )
        except KeyError:
            raise ValueError(f"Unsupported target attribute type: {condition.target_attribute_type}")   

        # Evaluate the condition based on the operator
        try:
            return self.operators[condition.operator](value, threshold)
        except KeyError:
            raise ValueError(f"Unsupported operator: {condition.operator}")
        
    def _get_next_node(self, active_process: "ActiveProcess", next_nodes: list[NextNode]) -> ActionNode | None:
        """
            This method evaluates the next nodes, checks the condtions and returns the next node to be set as the active node.
        """
        # Sort the next nodes. Nodes without a condtion should be evaluated last, since these are the ["Else"] conditions.
        next_nodes = sorted(next_nodes, key=lambda node: node.condition is None)
        for node in next_nodes:
            if node.condition and not self._evaluate_condition(active_process, node.condition):
                # Skip this node if the condition is not met
                continue
        
            # Condition is met, check the next value to determine the next node
            next_value = node.next
            if isinstance(next_value, list):
                return self._get_next_node(active_process, next_value)
            if isinstance(next_value, int):
                return self._get_action_node(next_value)
            if isinstance(next_value, str) and next_value == "END":
                return None
       
            raise ValueError(f"Rule {self.id} has a condition with an invalid next value: {next_value}")

        logger.warning(f"Rule {self.id} has no valid next nodes. This should not happen and is probably a misconfiguration when creating the workflow.")
        return None

    def evaluate_rule(self, active_process: "ActiveProcess") -> ActionNode | None:
        # TODO this currently only works for case study 1 and has to be adapted in the future
        if self.next:
            if self.next == "END":
                return None
            return self._get_action_node(int(self.next))
        
        # if there is no next node, we have to evaluate the condition.
        if not self.condition:
            raise ValueError(f"Rule {self.id} does not have a next node or condition.")
        
        # Evaluate the condition and get the next node
        return self._get_next_node(active_process, self.condition)

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

    def add_associated_instance(self, instance: models.Model) -> None:
        AssociatedModelInstance.objects.create(
            instance=instance,
            content_type=ContentType.objects.get_for_model(instance),
            instance_id=instance.pk,
            active_process=self,
        )
    
    def remove_associated_instance(self, instance: models.Model) -> None:
        AssociatedModelInstance.objects.get(
            instance=instance,
            content_type=ContentType.objects.get_for_model(instance),
            instance_id=instance.pk,
            active_process=self,
        ).delete()

    def complete_node(self, user: User | None) -> None:
        """Complete the current node and progress to the next node if needed."""
        if self.completed:
            raise ValueError("This process is already completed.")
        
        if user and self.active_node.actor not in user.roles:
            raise PermissionDenied(f"User {user.username} does not have the required role to complete this step.")
        
        # Evaluate the rule to determine the next node
        next_node = self.active_node.next_node_rule.evaluate_rule(self)
    
        if not next_node:
            self._complete_process(user)
            return
        self._progress_to_next_node(next_node, user)
    
    def reassign_user(self, new_user: User) -> None:
        """Reassign the current node to a new user."""
        if self.completed:
            raise ValueError("This process is already completed.")
        
        if self.active_node.actor not in new_user.roles:
            raise PermissionDenied(f"User {new_user.username} does not have the required role to complete this step.")
        
        if self.user == new_user:
            return
        
        # Log the reassignment of the current node
        ActionLog.objects.create(
            status="REASSIGNED",
            action_node=self.active_node,
            active_process=self,
            user=new_user,
        )
        self.user = new_user
        self.save()


    def _complete_process(self, user: User) -> None:
        """Mark the process as completed and log the completion."""
        self.completed = True
        self.save()
        ActionLog.objects.create(
            status="COMPLETED_PROCESS",
            action_node=self.active_node,
            active_process=self,
            user=user,
        )

    def _progress_to_next_node(self, next_node: ActionNode, user: User | None) -> None:
        """Progress to the next node and assign the next user."""

        # Log the completion of the current node
        ActionLog.objects.create(
            status="COMPLETED",
            action_node=self.active_node,
            active_process=self,
            user=user,
        )

        # Set the next node as the active node
        self.active_node = next_node
        self.save()

        # No task (for system or user) is assigned to the next node, so we can progress to the next node.
        if not self.active_node.url and not self.active_node.custom_code:
            return self._progress_to_next_node(next_node, user)

        # No URL means that the node is not a task node. Execute the custom_code if it exists.
        if not self.active_node.url and self.active_node.custom_code:
            ActionLog.objects.create(
                status="SYSTEM",
                action_node=next_node,
                active_process=self,
                user=None,
            )
            self._execute_custom_code()
            return self.complete_node(user)

        # Determine the next user for the task
        next_user = self._get_next_user(next_node, user)
        self.user = next_user
        self.save()

        # Log the assignment of the next node
        ActionLog.objects.create(
            status="STARTED",
            action_node=next_node,
            active_process=self,
            user=self.user,
        )
    
    def _get_next_user(self, next_node: ActionNode, current_user: User | None) -> User:
        """Determine the next user for the given node."""
        # Try to keep the current user for the next node
        if current_user and next_node.actor in current_user.roles:
            return current_user

        users = User.objects.filter(**{f"is_{next_node.actor}": True})
        # TODO: Implement a better distribution algorithm
        # For now, just return the first user that matches the actor
        next_user = users.first() if users.exists() else None
        if not next_user:
            raise ValueError(f"No user found for task {next_node}")
        return next_user

    def _execute_custom_code(self) -> None:
        assert self.active_node.custom_code, "Custom code is not defined for this node."
        module_name, function_name = self.active_node.custom_code.rsplit(".", 1)
        
        try:
            # Import the module and function dynamically
            module = importlib.import_module(module_name)
            custom_function = getattr(module, function_name)

            if not callable(custom_function):
                raise TypeError(f"{function_name} is not callable in module {module_name}")
            
            # Execute the custom function
            custom_function(active_process=self)
        except ImportError as e:
            raise ImportError(f"Fialed to import module when executing custom code: {module_name}") from e
        except AttributeError as e:
            raise AttributeError(f"Module {module_name} does not have function named {function_name}") from e
    
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
        ("STARTED", "Started next step"),
        ("COMPLETED", "Completed Step"),
        ("COMPLETED_PROCESS", "Completed Process"),
        ("STARTED_PROCESS", "Started Process"),
        ("REASSIGNED", "Reassigned to new user"),
        ("SYSTEM", "Executed system code"),
    ]

    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    action_node = models.ForeignKey(ActionNode, related_name="action_logs", on_delete=models.CASCADE)
    active_process = models.ForeignKey(ActiveProcess, related_name="active_process_action_logs", on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, related_name="action_logs", on_delete=models.CASCADE)

    def __str__(self):
        return f"Action log for {self.active_process} - {self.status} at {self.created_at}"