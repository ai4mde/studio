from uuid import UUID

from django.shortcuts import get_object_or_404
from ninja import Router

from metadata.api.helpers import create_instance, update_instance
from metadata.api.schemas.interface import (
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    InterfaceCreate,
    InterfaceRead,
    InterfaceSummary,
    InterfaceUpdate,
    PageCreate,
    PageRead,
    PageSectionCreate,
    PageSectionRead,
    PageSectionUpdate,
    PageUpdate,
    SectionAttributeCreate,
    SectionAttributeRead,
    SectionAttributeUpdate,
    SectionComponentCreate,
    SectionComponentRead,
    SectionComponentUpdate,
)
from metadata.models import (
    Category,
    Interface,
    Page,
    PageSection,
    SectionAttribute,
    SectionComponent,
)

router = Router()


# Interfaces


@router.get("/", response=list[InterfaceSummary])
def list_interfaces(request, system_id: UUID | None = None):
    interfaces = Interface.objects.all()

    if system_id is not None:
        interfaces = interfaces.filter(system_id=system_id)

    return interfaces


@router.get("/{interface_id}/", response=InterfaceRead)
def read_interface(request, interface_id: UUID):
    return get_object_or_404(
        Interface.objects.prefetch_related(
            "categories",
            "pages__page_sections",
            "sections__attributes",
        ),
        id=interface_id,
    )


@router.post("/", response=InterfaceRead)
def create_interface(request, payload: InterfaceCreate):
    return create_instance(Interface, payload)


@router.patch("/{interface_id}/", response=InterfaceRead)
def update_interface(request, interface_id: UUID, payload: InterfaceUpdate):
    interface = get_object_or_404(Interface, id=interface_id)
    return update_instance(interface, payload)


@router.delete("/{interface_id}/", response={204: None})
def delete_interface(request, interface_id: UUID):
    interface = get_object_or_404(Interface, id=interface_id)
    interface.delete()
    return 204, None


# Pages


@router.post("/pages/", response=PageRead)
def create_page(request, payload: PageCreate):
    return create_instance(Page, payload)


@router.patch("/pages/{page_id}/", response=PageRead)
def update_page(request, page_id: UUID, payload: PageUpdate):
    page = get_object_or_404(Page, id=page_id)
    return update_instance(page, payload)


@router.delete("/pages/{page_id}/", response={204: None})
def delete_page(request, page_id: UUID):
    page = get_object_or_404(Page, id=page_id)
    page.delete()
    return 204, None


# Categories


@router.post("/categories/", response=CategoryRead)
def create_category(request, payload: CategoryCreate):
    return create_instance(Category, payload)


@router.patch("/categories/{category_id}/", response=CategoryRead)
def update_category(request, category_id: UUID, payload: CategoryUpdate):
    category = get_object_or_404(Category, id=category_id)
    return update_instance(category, payload)


@router.delete("/categories/{category_id}/", response={204: None})
def delete_category(request, category_id: UUID):
    category = get_object_or_404(Category, id=category_id)
    category.delete()
    return 204, None


# Section components


@router.post("/sections/", response=SectionComponentRead)
def create_section(request, payload: SectionComponentCreate):
    return create_instance(SectionComponent, payload)


@router.patch("/sections/{section_id}/", response=SectionComponentRead)
def update_section(request, section_id: UUID, payload: SectionComponentUpdate):
    section = get_object_or_404(SectionComponent, id=section_id)
    return update_instance(section, payload)


@router.delete("/sections/{section_id}/", response={204: None})
def delete_section(request, section_id: UUID):
    section = get_object_or_404(SectionComponent, id=section_id)
    section.delete()
    return 204, None


# Page-section relationships


@router.post("/page-sections/", response=PageSectionRead)
def create_page_section(request, payload: PageSectionCreate):
    return create_instance(PageSection, payload)


@router.patch("/page-sections/{page_section_id}/", response=PageSectionRead)
def update_page_section(request, page_section_id: int, payload: PageSectionUpdate):
    page_section = get_object_or_404(PageSection, id=page_section_id)
    return update_instance(page_section, payload)


@router.delete("/page-sections/{page_section_id}/", response={204: None})
def delete_page_section(request, page_section_id: int):
    page_section = get_object_or_404(PageSection, id=page_section_id)
    page_section.delete()
    return 204, None


# Section-attribute relationships


@router.post("/section-attributes/", response=SectionAttributeRead)
def create_section_attribute(request, payload: SectionAttributeCreate):
    return SectionAttribute.objects.create(**payload.model_dump())


@router.patch("/section-attributes/{section_attribute_id}/", response=SectionAttributeRead)
def update_section_attribute(request, section_attribute_id: int, payload: SectionAttributeUpdate):
    section_attribute = get_object_or_404(SectionAttribute, id=section_attribute_id)
    return update_instance(section_attribute, payload)


@router.delete("/section-attributes/{section_attribute_id}/", response={204: None})
def delete_section_attribute(request, section_attribute_id: int):
    section_attribute = get_object_or_404(SectionAttribute, id=section_attribute_id)
    section_attribute.delete()
    return 204, None