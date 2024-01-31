from django.db import models
from uuid import uuid4

class Pipeline(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    requirements = models.TextField(default='')
    output = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    type = models.CharField(max_length=100, default='metadata')
    step = models.SmallIntegerField(default=2) # Creating is step 1, requirements is step 2, running is step 3, finished is step 4
    url = models.CharField(max_length=100, default='http://tiantian-class.ai4mde-prose.localhost/')
