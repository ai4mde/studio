from ninja import ModelSchema

from metadata.models import (
    Category,
    Interface,
    Page,
    PageSection,
    SectionAttribute,
    SectionComponent,
)


class InterfaceRead(ModelSchema):
    class Meta:
        model = Interface
        fields = "__all__"


class InterfaceCreate(ModelSchema):
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


class PageRead(ModelSchema):
    class Meta:
        model = Page
        fields = "__all__"


class PageCreate(ModelSchema):
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
        fields = "__all__"


class CategoryCreate(ModelSchema):
    class Meta:
        model = Category
        fields = [
            "interface",
            "name",
        ]


class CategoryUpdate(ModelSchema):
    class Meta:
        model = Category
        fields = ["name"]
        fields_optional = "__all__"


class SectionComponentRead(ModelSchema):
    class Meta:
        model = SectionComponent
        fields = "__all__"


class SectionComponentCreate(ModelSchema):
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


class PageSectionRead(ModelSchema):
    class Meta:
        model = PageSection
        fields = "__all__"


class PageSectionCreate(ModelSchema):
    class Meta:
        model = PageSection
        fields = [
            "page",
            "section",
            "order",
        ]


class PageSectionUpdate(ModelSchema):
    class Meta:
        model = PageSection
        fields = ["order"]
        fields_optional = "__all__"


class SectionAttributeRead(ModelSchema):
    class Meta:
        model = SectionAttribute
        fields = "__all__"


class SectionAttributeCreate(ModelSchema):
    class Meta:
        model = SectionAttribute
        fields = [
            "section",
            "attribute",
            "order",
        ]


class SectionAttributeUpdate(ModelSchema):
    class Meta:
        model = SectionAttribute
        fields = ["order"]
        fields_optional = "__all__"