import importlib
import json
import logging
from operator import eq, ne, lt, le, gt, ge
import re
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
    next: Union[int, str, list[int], list["NextNode"]]
    condition: Condition | None = None
    check: int | None = None


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
                next=item['next'] if isinstance(item['next'], list) and all(isinstance(n, int) for n in item['next']) else (
                    self._to_structured_format(item['next']) if isinstance(item['next'], list) else item['next']
                ),
                condition=Condition(**{key: item['condition'][key] for key in Condition._fields}) if 'condition' in item else None,
                check=item.get('check'),
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

    def execute_custom_code(self, active_process: "ActiveProcess") -> None:
        # No custom code to execute
        if not self.custom_code:
            return

        module_name, function_name = self.custom_code.rsplit(".", 1)
        
        try:
            # Import the module and function dynamically
            module = importlib.import_module(module_name)
            custom_function = getattr(module, function_name)

            if not callable(custom_function):
                raise TypeError(f"{function_name} is not callable in module {module_name}")
            
            # Execute the custom function
            custom_function(active_process=active_process)
        except ImportError as e:
            raise ImportError(f"Failled to import module when executing custom code: {module_name}") from e
        except AttributeError as e:
            raise AttributeError(f"Module {module_name} does not have function named {function_name}") from e
 
    def _get_next_user(self, current_user: User | None) -> User | None:
        """Determine the next user for the given node."""
        # No user assignment if there is nothing to do for the user
        if not self.url:
            return None

        # Try to keep the current user for the next node
        if current_user and self.actor in current_user.roles:
            return current_user

        users = User.objects.filter(**{f"is_{self.actor}": True})
        # TODO: Implement a better distribution algorithm
        # For now, just return the first user that matches the actor
        next_user = users.first() if users.exists() else None
        logger.warning(f"No user found for actor {self.actor}. The user assignment for this node will have to be done manually.")
        return next_user

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

    def start_process(self, user: User) -> "ActiveProcessNode":
        """Start a process for the given user."""
        assert self.start_node # TODO make start node required. This involves changing the workflow population migration.
        if self.start_node.actor not in user.roles:
            raise PermissionDenied(f"User {user.username} does not have the required role to start this process.")

        # Create the active process
        active_process = ActiveProcess.objects.create(process=self)

        # Set the start node as the active node
        active_process_node = ActiveProcessNode.objects.create(
            active_process=active_process,
            action_node=self.start_node,
            user=user,
        )

        # Log the start of the process
        ActionLog.objects.create(
            status="STARTED_PROCESS",
            action_node=self.start_node,
            active_process=active_process,
            user=user,
        )
        return active_process_node

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

    @property
    def next_nodes(self) -> list[ActionNode] | None:
        if self.next is None or self.next == "END":
            return None
        if self.next.isnumeric():
            return [self._get_action_node(int(self.next))]

        match = re.findall(r'\d+', self.next)
        if match:
            return [self._get_action_node(int(n)) for n in match]
        return None

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
    
    def _check_convergence_point(self, active_process: "ActiveProcess", convergence_point_id: int) -> bool:
        """
            Check if the convergence point is completed, marking parallel controlflows can be merged.
            This method will also track the number of nodes that have reached the convergence point.
        """
        convergence_point = ActiveConvergencePoint.objects.filter(
            active_process=active_process,
            convergence_point__id=convergence_point_id,
        )

        # If there are multiple convergence points, throw an error
        if convergence_point.count() > 1:
            raise ValueError(f"Rule {self.id} has multiple convergence points with the same id: {convergence_point_id}. This should not happen.")
        
        convergence_point = convergence_point.first()

        if not convergence_point:
            # This is the first node to reach the convergence point. Create it.
            ActiveConvergencePoint.objects.create(
                active_process=active_process,
                convergence_point=ConvergencePoint.objects.get(id=convergence_point_id),
            )
            return False
        else:
            # The convergence point is here, add a count to denote a new node has reached it.
            convergence_point.count += 1
            convergence_point.save()

            # If the convergence point is not completed, we can't continue to the next node.
            if not convergence_point.completed:
                return False
            # The convergence point is completed, delete it and continue to the next node.
            else:
                convergence_point.delete()
                return True
        
    def _get_next_node(self, active_process: "ActiveProcess", next_nodes: list[NextNode]) -> list[ActionNode] | None:
        """
            This method evaluates the next nodes, checks the condtions and returns the next node to be set as the active node.
        """
        # Sort the next nodes. Nodes without a condtion should be evaluated last, since these are the ["Else"] conditions.
        next_nodes = sorted(next_nodes, key=lambda node: node.condition is None)
        for node in next_nodes:
            if node.condition and not self._evaluate_condition(active_process, node.condition):
                # Skip this node if the condition is not met
                continue
            
            # The node is behind a convergence point. We need to check if the convergence point is completed.
            # If it is not, we can't continue to the next node.
            if node.check is not None and not self._check_convergence_point(active_process, node.check):
                return None

            # Condition is met, check the next value to determine the next node
            next_value = node.next
            if isinstance(next_value, list):
                if all(isinstance(n, int) for n in next_value):
                    return [self._get_action_node(n) for n in next_value]
                return self._get_next_node(active_process, next_value)
            if isinstance(next_value, int):
                return [self._get_action_node(next_value)]
            if isinstance(next_value, str) and next_value == "END":
                return None
       
            raise ValueError(f"Rule {self.id} has a condition with an invalid next value: {next_value}")

        logger.warning(f"Rule {self.id} has no valid next nodes. This should not happen and is probably a misconfiguration when creating the workflow.")
        return None

    def evaluate_rule(self, active_process: "ActiveProcess") -> list[ActionNode] | None:
        # Check if the next nodes are directly set in the rule
        if self.next_nodes is not None or self.next == "END":
            return self.next_nodes

        # if there is no next node directly set, we have to evaluate the condition.
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
    active_nodes = models.ManyToManyField(
        ActionNode,
        related_name="active_processes",
        through="ActiveProcessNode",
    )
    active_convergence_points = models.ManyToManyField(
        "ConvergencePoint",
        related_name="active_processes",
        through="ActiveConvergencePoint",
    )

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

    def _complete_process(self, user: User) -> None:
        """Mark the process as completed and log the completion."""
        # Remove all active nodes from this process
        ActiveProcessNode.objects.filter(active_process=self).delete()

        # Log the completion of the process
        ActionLog.objects.create(
            status="COMPLETED_PROCESS",
            action_node=None,
            active_process=self,
            user=user,
        )

        # Mark the process as completed
        self.completed = True
        self.save()

    def __str__(self):
        return f"Active process for {self.process}"


class ActiveProcessNode(models.Model):
    class Meta:
        unique_together = ("active_process", "action_node")

    id = models.AutoField(primary_key=True)
    active_process = models.ForeignKey(ActiveProcess, on_delete=models.CASCADE)
    action_node = models.ForeignKey(ActionNode, on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def reassign_user(self, new_user: User) -> None:
        """Reassign the current node to a new user."""
        if self.active_process.completed:
            raise ValueError("This process is already completed.")
        
        if self.action_node.actor not in new_user.roles:
            raise PermissionDenied(f"User {new_user.username} does not have the required role to complete this step.")
        
        if self.user == new_user:
            return
        
        # Log the reassignment of the current node
        ActionLog.objects.create(
            status="REASSIGNED",
            action_node=self.action_node,
            active_process=self.active_process,
            user=new_user,
        )
        self.user = new_user
        self.save()

    def complete_node(self, user: User | None) -> None:
        """Complete the current node and progress to the next node if needed."""
        if self.active_process.completed:
            self.delete()
            raise ValueError("This process has already been completed")
        
        if user and self.action_node.actor not in user.roles:
            raise PermissionDenied(f"User {user.username} does not have the required role to complete this step.")
        
        # Evaluate the rule to determine the next node
        next_nodes = self.action_node.next_node_rule.evaluate_rule(self.active_process)

        # Only progress to the next node if there is one
        if not next_nodes:
            # Mark the current node as completed and delete it as an active node
            self._log_action("COMPLETED", user)
            self.delete()

            # If there are no next nodes, we can complete the process
            if not ActiveProcessNode.objects.filter(active_process=self.active_process).exists():
                self.active_process._complete_process(user)
            return

        # Progress to the next node
        self._progress_to_next_node(next_nodes, user)

    def _progress_to_next_node(self, next_nodes: list[ActionNode], user: User | None) -> None:
        """Progress to the next node and assign the next user."""
        # Log the completion of the current node
        self._log_action("COMPLETED", user)

        for next_node in next_nodes:
            # If the node is already active, skip it
            if ActiveProcessNode.objects.filter(active_process=self.active_process, action_node=next_node).exists():
                continue

            # Assign a user and mark the next node as active for this process
            next_user = next_node._get_next_user(user)
            ActiveProcessNode.objects.create(
                active_process=self.active_process,
                action_node=next_node,
                user=next_user,
            )

            # Log the start of the next node
            self._log_action("STARTED", next_user, next_node)
        
        # Complete all nodes that should be completed without any user interaction.
        self._complete_unattended_nodes(None)

        # Remove the current node as an active node, since it is now completed
        self.delete()

        # Complete the process if there are no active nodes left
        if not ActiveProcessNode.objects.filter(active_process=self.active_process).exists():
            self.active_process._complete_process(user)

    def _complete_unattended_nodes(self, user: User | None) -> None:
        """
            Complete all nodes that should be completed without any user interaction.
            This includes custom code nodes and nodes without a URL.
        """
        custom_code_nodes = ActiveProcessNode.objects.filter(
            active_process=self.active_process,
            action_node__custom_code__isnull=False,
            action_node__url__isnull=True,
        )

        # Execute custom code for nodes and progress to the next node
        for process_node in custom_code_nodes:
            process_node.action_node.execute_custom_code(self.active_process)
            process_node.complete_node(user)
        
        empty_nodes = ActiveProcessNode.objects.filter(
            active_process=self.active_process,
            action_node__url__isnull=True,
            action_node__custom_code__isnull=True,
        )

        # Complete any node that does not have any action linked to it.
        for process_node in empty_nodes:
            logger.warning(
                f"Node {process_node.action_node} has no URL and no custom code. This should not happen and is probably a misconfiguration when creating the workflow."
                "The node will be completed automatically."
            )
            process_node.complete_node(user)

    def _log_action(self, status: str, user: User | None, next_node: ActionNode | None = None) -> None:
        ActionLog.objects.create(
            status=status,
            action_node=self.action_node if next_node is None else next_node,
            active_process=self.active_process,
            user=user,
        )

class AssociatedModelInstance(models.Model):
    id = models.AutoField(primary_key=True)
    instance_id = models.IntegerField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    instance = GenericForeignKey('content_type', 'instance_id')
    active_process = models.ForeignKey(ActiveProcess, related_name="associated_model_instances", on_delete=models.PROTECT)

    def __str__(self):
        return f"Instance {self.instance_id} of {self.content_type.name}"


class ConvergencePoint(models.Model):
    id = models.AutoField(primary_key=True)
    required_count = models.IntegerField()
    process = models.ForeignKey(Process, related_name="convergence_points", on_delete=models.CASCADE)

    def __str__(self):
        return f"Convergence point for {self.process} with {self.required_count} required nodes"


class ActiveConvergencePoint(models.Model):
    id = models.AutoField(primary_key=True)
    active_process = models.ForeignKey(ActiveProcess, related_name="awaiting_convergence_points", on_delete=models.CASCADE)
    convergence_point = models.ForeignKey(ConvergencePoint, related_name="active_convergence_points", on_delete=models.CASCADE)
    count = models.IntegerField(default=1)

    @property
    def completed(self) -> bool:
        return self.count >= self.convergence_point.required_count

    def __str__(self):
        return f"Active convergence point {self.convergence_point} for process {self.active_process}"


class ActionLog(models.Model):
    STATUS_CHOICES = [
        ("STARTED", "Started next step"),
        ("COMPLETED", "Completed Step"),
        ("COMPLETED_PROCESS", "Completed Process"),
        ("STARTED_PROCESS", "Started Process"),
        ("REASSIGNED", "Reassigned to new user"),
        ("SYSTEM", "Executed system code"),
        ("CANCELLED", "Cancelled Process"),
    ]

    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    action_node = models.ForeignKey(ActionNode, related_name="action_logs", on_delete=models.CASCADE, null=True)
    active_process = models.ForeignKey(ActiveProcess, related_name="active_process_action_logs", on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, related_name="action_logs", on_delete=models.CASCADE)

    def __str__(self):
        return f"Action log for {self.active_process} - {self.status} at {self.created_at}"
