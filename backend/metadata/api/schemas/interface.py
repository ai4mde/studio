from uuid import UUID

from ninja import Field, ModelSchema

from metadata.models import (
    Category,
    Interface,
    Page,
    PageSection,
    SectionAttribute,
    SectionComponent,
)


# Django Ninja infers int for foreign keys to models whose primary key is
# a OneToOneField referencing a UUID. Explicitly annotate these as UUID.

class PageSectionRead(ModelSchema):
    class Meta:
        model = PageSection
        fields = ["page", "section", "order"]


class PageSectionCreate(ModelSchema):
    class Meta:
        model = PageSection
        fields = ["page", "section", "order"]
        fields_optional = ["order"]


class PageSectionUpdate(ModelSchema):
    class Meta:
        model = PageSection
        fields = ["order"]
        fields_optional = "__all__"


class PageRead(ModelSchema):
    action: UUID | None = Field(None, alias="action_id")
    page_sections: list[PageSectionRead] = []

    class Meta:
        model = Page
        fields = [
            "id",
            "interface",
            "name",
            "type",
            "action",
            "category",
        ]


class PageCreate(ModelSchema):
    action: UUID | None = Field(None, alias="action_id")

    class Meta:
        model = Page
        fields = [
            "interface",
            "name",
            "type",
            "action",
            "category",
        ]


class PageUpdate(ModelSchema):
    action: UUID | None = Field(None, alias="action_id")

    class Meta:
        model = Page
        fields = [
            "name",
            "type",
            "action",
            "category",
        ]
        fields_optional = "__all__"


class CategoryRead(ModelSchema):
    class Meta:
        model = Category
        fields = ["id", "interface", "name"]


class CategoryCreate(ModelSchema):
    class Meta:
        model = Category
        fields = ["interface", "name"]


class CategoryUpdate(ModelSchema):
    class Meta:
        model = Category
        fields = ["name"]
        fields_optional = "__all__"


class SectionAttributeRead(ModelSchema):
    class Meta:
        model = SectionAttribute
        fields = ["id", "section", "attribute", "order"]


class SectionAttributeCreate(ModelSchema):
    class Meta:
        model = SectionAttribute
        fields = ["section", "attribute", "order"]


class SectionAttributeUpdate(ModelSchema):
    class Meta:
        model = SectionAttribute
        fields = ["order"]
        fields_optional = "__all__"


class SectionComponentRead(ModelSchema):
    uml_class: UUID | None = Field(None, alias="uml_class_id")
    attributes: list[SectionAttributeRead] = []

    class Meta:
        model = SectionComponent
        fields = [
            "id",
            "interface",
            "name",
            "text",
            "uml_class",
            "allow_create",
            "allow_update",
            "allow_delete",
        ]


class SectionComponentCreate(ModelSchema):
    uml_class: UUID | None = Field(None, alias="uml_class_id")

    class Meta:
        model = SectionComponent
        fields = [
            "interface",
            "name",
            "text",
            "uml_class",
            "allow_create",
            "allow_update",
            "allow_delete",
        ]


class SectionComponentUpdate(ModelSchema):
    uml_class: UUID | None = Field(None, alias="uml_class_id")

    class Meta:
        model = SectionComponent
        fields = [
            "name",
            "text",
            "uml_class",
            "allow_create",
            "allow_update",
            "allow_delete",
        ]
        fields_optional = "__all__"


class InterfaceSummary(ModelSchema):
    class Meta:
        model = Interface
        fields = ["id", "system", "name", "description"]


class InterfaceRead(ModelSchema):
    actor: UUID | None = Field(None, alias="actor_id")
    pages: list[PageRead]
    categories: list[CategoryRead]
    sections: list[SectionComponentRead]

    class Meta:
        model = Interface
        fields = [
            "id",
            "system",
            "name",
            "description",
            "actor",
            "radius",
            "text_color",
            "accent_color",
            "background_color",
            "style",
            "manager_access",
        ]


class InterfaceCreate(ModelSchema):
    actor: UUID | None = Field(None, alias="actor_id")

    class Meta:
        model = Interface
        fields = [
            "system",
            "name",
            "description",
            "actor",
            "radius",
            "text_color",
            "accent_color",
            "background_color",
            "style",
            "manager_access",
        ]


class InterfaceUpdate(ModelSchema):
    actor: UUID | None = Field(None, alias="actor_id")


    class Meta:
        model = Interface
        fields = [
            "name",
            "description",
            "actor",
            "radius",
            "text_color",
            "accent_color",
            "background_color",
            "style",
            "manager_access",
        ]
        fields_optional = "__all__"
