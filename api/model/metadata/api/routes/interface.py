from uuid import UUID

from django.shortcuts import get_object_or_404
from ninja import Router

from metadata.api.schemas.interface import (
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    InterfaceCreate,
    InterfaceRead,
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


@router.get("/interfaces/", response=list[InterfaceRead])
def list_interfaces(request, system_id: UUID | None = None):
    interfaces = Interface.objects.all()

    if system_id:
        interfaces = interfaces.filter(system_id=system_id)

    return interfaces


@router.get("/interfaces/{interface_id}/", response=InterfaceRead)
def read_interface(request, interface_id: UUID):
    return get_object_or_404(Interface, id=interface_id)


@router.post("/interfaces/", response=InterfaceRead)
def create_interface(request, payload: InterfaceCreate):
    return Interface.objects.create(**payload.model_dump())


@router.patch("/interfaces/{interface_id}/", response=InterfaceRead)
def update_interface(request, interface_id: UUID, payload: InterfaceUpdate):
    interface = get_object_or_404(Interface, id=interface_id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(interface, field, value)

    interface.save()
    return interface


@router.delete("/interfaces/{interface_id}/", response={204: None})
def delete_interface(request, interface_id: UUID):
    interface = get_object_or_404(Interface, id=interface_id)
    interface.delete()
    return 204, None


# Pages


@router.get("/pages/", response=list[PageRead])
def list_pages(request, interface_id: UUID | None = None):
    pages = Page.objects.all()

    if interface_id:
        pages = pages.filter(interface_id=interface_id)

    return pages


@router.get("/pages/{page_id}/", response=PageRead)
def read_page(request, page_id: UUID):
    return get_object_or_404(Page, id=page_id)


@router.post("/pages/", response=PageRead)
def create_page(request, payload: PageCreate):
    return Page.objects.create(**payload.model_dump())


@router.patch("/pages/{page_id}/", response=PageRead)
def update_page(request, page_id: UUID, payload: PageUpdate):
    page = get_object_or_404(Page, id=page_id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(page, field, value)

    page.save()
    return page


@router.delete("/pages/{page_id}/", response={204: None})
def delete_page(request, page_id: UUID):
    page = get_object_or_404(Page, id=page_id)
    page.delete()
    return 204, None


# Categories


@router.get("/categories/", response=list[CategoryRead])
def list_categories(request, interface_id: UUID | None = None):
    categories = Category.objects.all()

    if interface_id:
        categories = categories.filter(interface_id=interface_id)

    return categories


@router.get("/categories/{category_id}/", response=CategoryRead)
def read_category(request, category_id: UUID):
    return get_object_or_404(Category, id=category_id)


@router.post("/categories/", response=CategoryRead)
def create_category(request, payload: CategoryCreate):
    return Category.objects.create(**payload.model_dump())


@router.patch("/categories/{category_id}/", response=CategoryRead)
def update_category(request, category_id: UUID, payload: CategoryUpdate):
    category = get_object_or_404(Category, id=category_id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, field, value)

    category.save()
    return category


@router.delete("/categories/{category_id}/", response={204: None})
def delete_category(request, category_id: UUID):
    category = get_object_or_404(Category, id=category_id)
    category.delete()
    return 204, None


# Section components


@router.get("/sections/", response=list[SectionComponentRead])
def list_sections(request, interface_id: UUID | None = None):
    sections = SectionComponent.objects.all()

    if interface_id:
        sections = sections.filter(interface_id=interface_id)

    return sections


@router.get("/sections/{section_id}/", response=SectionComponentRead)
def read_section(request, section_id: UUID):
    return get_object_or_404(SectionComponent, id=section_id)


@router.post("/sections/", response=SectionComponentRead)
def create_section(request, payload: SectionComponentCreate):
    return SectionComponent.objects.create(**payload.model_dump())


@router.patch("/sections/{section_id}/", response=SectionComponentRead)
def update_section(
    request,
    section_id: UUID,
    payload: SectionComponentUpdate,
):
    section = get_object_or_404(SectionComponent, id=section_id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(section, field, value)

    section.save()
    return section


@router.delete("/sections/{section_id}/", response={204: None})
def delete_section(request, section_id: UUID):
    section = get_object_or_404(SectionComponent, id=section_id)
    section.delete()
    return 204, None


# Page-section relationships


@router.get("/page-sections/", response=list[PageSectionRead])
def list_page_sections(request, page_id: UUID | None = None):
    page_sections = PageSection.objects.all()

    if page_id:
        page_sections = page_sections.filter(page_id=page_id)

    return page_sections


@router.post("/page-sections/", response=PageSectionRead)
def create_page_section(request, payload: PageSectionCreate):
    return PageSection.objects.create(**payload.model_dump())


@router.patch(
    "/page-sections/{page_section_id}/",
    response=PageSectionRead,
)
def update_page_section(
    request,
    page_section_id: int,
    payload: PageSectionUpdate,
):
    page_section = get_object_or_404(PageSection, id=page_section_id)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(page_section, field, value)

    page_section.save()
    return page_section


@router.delete(
    "/page-sections/{page_section_id}/",
    response={204: None},
)
def delete_page_section(request, page_section_id: int):
    page_section = get_object_or_404(PageSection, id=page_section_id)
    page_section.delete()
    return 204, None


# Section-attribute relationships


@router.get(
    "/section-attributes/",
    response=list[SectionAttributeRead],
)
def list_section_attributes(
    request,
    section_id: UUID | None = None,
):
    section_attributes = SectionAttribute.objects.all()

    if section_id:
        section_attributes = section_attributes.filter(section_id=section_id)

    return section_attributes


@router.post(
    "/section-attributes/",
    response=SectionAttributeRead,
)
def create_section_attribute(
    request,
    payload: SectionAttributeCreate,
):
    return SectionAttribute.objects.create(**payload.model_dump())


@router.patch(
    "/section-attributes/{section_attribute_id}/",
    response=SectionAttributeRead,
)
def update_section_attribute(
    request,
    section_attribute_id: int,
    payload: SectionAttributeUpdate,
):
    section_attribute = get_object_or_404(
        SectionAttribute,
        id=section_attribute_id,
    )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(section_attribute, field, value)

    section_attribute.save()
    return section_attribute


@router.delete(
    "/section-attributes/{section_attribute_id}/",
    response={204: None},
)
def delete_section_attribute(
    request,
    section_attribute_id: int,
):
    section_attribute = get_object_or_404(
        SectionAttribute,
        id=section_attribute_id,
    )
    section_attribute.delete()
    return 204, None