import uuid

from django.db import models
from metadata.models import Project

#class TimeStampedModel(models.Model):
#    """
#    Abstract base class that adds created_at and updated_at fields to models.
#    """
#    created_at = models.DateTimeField(auto_now_add=True)
#    updated_at = models.DateTimeField(auto_now=True)
#
#    class Meta:
#        abstract = True
#

#class SRSDocument(TimeStampedModel):
class SRSDocument(models.Model):
    """
    Model for storing SRS documents metadata. The actual SRS document is stored in a file on the 
    server or in a S3 bucket. Which one will be descided later.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    version = models.CharField(max_length=8)
    description = models.TextField()
    path = models.CharField(max_length=255)