import uuid

from django.db import models

from .types import InterfaceStyle, PageType

class Interface(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    system = models.ForeignKey(
        "System",
        on_delete=models.CASCADE,
        related_name="interfaces",
    )
    name = models.CharField(max_length=255)
    description = models.TextField()
    actor = models.ForeignKey(
        "Actor",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="interfaces",
    )
    
    # Styling
    radius = models.PositiveIntegerField(default=0)
    text_color = models.CharField(max_length=7, default="#000000")
    accent_color = models.CharField(max_length=7, default="#F5F5F4")
    background_color = models.CharField(max_length=7, default="#FFFFFF")
    style = models.CharField(max_length=20, choices=InterfaceStyle.choices, default=InterfaceStyle.MODERN)

    # Settings
    manager_access = models.BooleanField(default=True)


class Page(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    interface = models.ForeignKey(
        Interface,
        on_delete=models.CASCADE,
        related_name="pages",
    )
    name = models.CharField(max_length=255)
    type = models.CharField(
        max_length=20,
        choices=PageType.choices,
        default=PageType.NORMAL,
    )
    action = models.ForeignKey(
        "Action",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pages",
    )
    category = models.ForeignKey(
        "Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pages",
    )


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    interface = models.ForeignKey(
        Interface,
        on_delete=models.CASCADE,
        related_name="categories",
    )
    name = models.CharField(max_length=255)


class SectionComponent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    interface = models.ForeignKey(
        Interface,
        on_delete=models.CASCADE,
        related_name="sections",
    )
    name = models.CharField(max_length=255)
    text = models.CharField(max_length=255, blank=True, default="")
    uml_class = models.ForeignKey(
        "Class",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="section_components",
    )
    allow_create = models.BooleanField(default=False)
    allow_update = models.BooleanField(default=False)
    allow_delete = models.BooleanField(default=False)


class PageSection(models.Model):
    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
        related_name="page_sections",
    )
    section = models.ForeignKey(
        SectionComponent,
        on_delete=models.CASCADE,
        related_name="page_sections",
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["page", "order"],
                name="unique_page_section_order",
            ),
            models.UniqueConstraint(
                fields=["page", "section"],
                name="unique_page_section",
            ),
        ]
    

class SectionAttribute(models.Model):
    section = models.ForeignKey(
        SectionComponent,
        on_delete=models.CASCADE,
        related_name="attributes",
    )
    attribute = models.ForeignKey(
        "Attribute",
        on_delete=models.CASCADE,
        related_name="section_attributes",
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["section", "order"],
                name="unique_section_attribute_order",
            ),
            models.UniqueConstraint(
                fields=["section", "attribute"],
                name="unique_section_attribute",
            ),
        ]