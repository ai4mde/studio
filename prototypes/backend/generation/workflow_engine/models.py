from django.db import models
from django.db.models.manager import RelatedManager


class AssociatedModel(models.Model):
    class_name = models.CharField(max_length=255)

    def __str__(self):
        return self.class_name


class ActionNode(models.Model):
    actor = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    is_end_node = models.BooleanField(default=False)
    process = models.ForeignKey("Process", related_name="action_nodes", on_delete=models.CASCADE)

    def get_next_node(self):
        raise NotImplementedError

    def __str__(self):
        return f"{self.actor} - {self.name}"


class Process(models.Model):
    name = models.CharField(max_length=255)
    start_node = models.ForeignKey(ActionNode, related_name="start_node", on_delete=models.PROTECT)
    associated_models = models.ManyToManyField(AssociatedModel, related_name="processes")
    action_nodes: RelatedManager[ActionNode]

    @property
    def end_nodes(self):
        return self.action_nodes.filter(is_end_node=True)

    def start_process(self):
        raise NotImplementedError

    def __str__(self):
        return self.name


class Rule(models.Model):
    condition = models.JSONField(default=dict)
    action_node = models.OneToOneField(ActionNode, related_name="rule", on_delete=models.CASCADE)

    def evaluate_rule(self):
        raise NotImplementedError

    def __str__(self):
        return f"Next node rule for {self.action_node}"

class ActiveProcess(models.Model):
    completed = models.BooleanField(default=False)
    process = models.ForeignKey(Process, related_name="active_processes", on_delete=models.CASCADE)
    active_node = models.ForeignKey(ActionNode, related_name="active_processes", on_delete=models.PROTECT)

    def complete_node(self):
        raise NotImplementedError

    def __str__(self):
        return f"Active process for {self.process}"

class AssociatedModelInstance(models.Model):
    instanceId = models.IntegerField()
    associated_model = models.ForeignKey(AssociatedModel, related_name="instances", on_delete=models.PROTECT)
    active_process = models.ForeignKey(ActiveProcess, related_name="associated_model_instances", on_delete=models.PROTECT)

    def __str__(self):
        return f"Instance {self.instanceId} of {self.associated_model}"
