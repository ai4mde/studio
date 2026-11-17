import type { InterfaceRead } from "../../../api/metadata/interface";
import {
    createCategory,
    createPage,
    createPageSection,
    createSection,
    createSectionAttribute,
    deleteCategory,
    deletePage,
    deleteSection,
} from "../../../api/metadata/interfaceComponents";
import { editorToContent } from "./content";

// The backend saves categories, sections and pages one by one. Like the old
// single save, replace everything: delete what the interface has now, then
// create what the editor has, mapping the editor's ids to the new ones.
export const saveInterfaceContent = async (
    current: InterfaceRead,
    categories: any[],
    pages: any[],
    sections: any[],
) => {
    const content = editorToContent(categories, pages, sections);
    const interfaceId = current.id!;

    // Deleting pages and sections also removes their page-sections and section-attributes
    for (const page of current.pages) {
        await deletePage(page.id!);
    }
    for (const section of current.sections) {
        await deleteSection(section.id!);
    }
    for (const category of current.categories) {
        await deleteCategory(category.id!);
    }

    const categoryIds: Record<string, string> = {};
    for (const category of content.categories) {
        const created = await createCategory({
            interface_id: interfaceId,
            name: category.name,
        });
        categoryIds[category.id] = created.id!;
    }

    const sectionIds: Record<string, string> = {};
    for (const section of content.sections) {
        const created = await createSection({
            interface_id: interfaceId,
            name: section.name,
            text: section.text,
            uml_class_id: section.uml_class,
            allow_create: section.allow_create,
            allow_update: section.allow_update,
            allow_delete: section.allow_delete,
        });
        sectionIds[section.id] = created.id!;

        for (const [order, attributeId] of section.attributes.entries()) {
            await createSectionAttribute({
                section_id: created.id!,
                attribute_id: attributeId,
                order,
            });
        }
    }

    for (const page of content.pages) {
        const created = await createPage({
            interface_id: interfaceId,
            name: page.name,
            type: page.type,
            action_id: page.action,
            category_id: page.category ? categoryIds[page.category] ?? null : null,
        });

        // Only link sections that still exist in the editor
        const pageSectionIds = page.sections
            .map((sectionId) => sectionIds[sectionId])
            .filter(Boolean);

        for (const [order, sectionId] of pageSectionIds.entries()) {
            await createPageSection({
                page_id: created.id!,
                section_id: sectionId,
                order,
            });
        }
    }
};
