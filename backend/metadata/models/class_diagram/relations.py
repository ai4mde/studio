from django.db import models

from ..relation import RelationDataModel


class Multiplicity(models.Model):
    """
        Relation multiplicity for association and composition

        Examples:
            1       => lower=1, upper=1
            0..1    => lower=0, upper=1   
            0..*    => lower=0, upper=None
            1..*    => lower=1, upper=None       
    """
    source_lower = models.PositiveIntegerField()
    source_upper = models.PositiveIntegerField(blank=True, null=True)

    target_lower = models.PositiveIntegerField()
    target_upper = models.PositiveIntegerField(blank=True, null=True)


class EndpointLabel(models.Model):
    """
        Endpoint labels for relations
    """
    source = models.CharField(max_length=255, blank=True, default="")
    target = models.CharField(max_length=255, blank=True, default="")


class MultiplicityAndLabelsMixin:
    """
        Lets the API send multiplicity and labels as nested values.
        The rows in Multiplicity and EndpointLabel are created and
        updated here, so the frontend never has to know their ids.
    """

    @classmethod
    def prepare_data(cls, data):
        data = dict(data)

        # The edge route drops unset values, so fill in the defaults here
        multiplicity = {
            "source_lower": 1,
            "source_upper": 1,
            "target_lower": 1,
            "target_upper": 1,
            **(data.get("multiplicity") or {}),
        }
        instance = Multiplicity(**multiplicity)
        instance.full_clean()
        instance.save()
        data["multiplicity"] = instance.id

        labels = {
            "source": "",
            "target": "",
            **(data.get("labels") or {}),
        }
        instance = EndpointLabel(**labels)
        instance.full_clean()
        instance.save()
        data["labels"] = instance.id

        return data

    def prepare_update(self, data):
        data = dict(data)

        for field in ("multiplicity", "labels"):
            values = data.pop(field, None)
            if values is None:
                continue

            related = getattr(self, field)
            for name, value in values.items():
                setattr(related, name, value)
            related.full_clean()
            related.save()

        return data


class Association(MultiplicityAndLabelsMixin, RelationDataModel):
    derived = models.BooleanField(default=False)
    label = models.CharField(max_length=255, blank=True, default="")
    multiplicity = models.OneToOneField(
        Multiplicity,
        on_delete=models.CASCADE,
        related_name="association",
    )
    labels = models.OneToOneField(
        EndpointLabel,
        on_delete=models.CASCADE,
        related_name="association",
    )


class Composition(MultiplicityAndLabelsMixin, RelationDataModel):
    label = models.CharField(max_length=255, blank=True, default="")
    multiplicity = models.OneToOneField(
        Multiplicity,
        on_delete=models.CASCADE,
        related_name="composition",
    )
    labels = models.OneToOneField(
        EndpointLabel,
        on_delete=models.CASCADE,
        related_name="composition",
    )


class Dependency(RelationDataModel):
    label = models.CharField(max_length=255, blank=True, default="")
