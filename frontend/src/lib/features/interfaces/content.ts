import type { InterfaceRead } from "../../../api/metadata/interface";

// The editor's content with plain ids, the step between its localStorage
// shapes and the separate category/section/page endpoints
export type EditorContent = {
    categories: { id: string; name: string }[];
    sections: {
        id: string;
        name: string;
        text: string;
        uml_class: string | null;
        allow_create: boolean;
        allow_update: boolean;
        allow_delete: boolean;
        attributes: string[];
    }[];
    pages: {
        id: string;
        name: string;
        type: string;
        category: string | null;
        action: string | null;
        sections: string[];
    }[];
};

// The editor keeps its old (localStorage) shapes; convert them for the API
export const editorToContent = (
    categories: any[],
    pages: any[],
    sections: any[],
): EditorContent => ({
    categories: categories.map((c) => ({
        id: c.id,
        name: c.name ?? "",
    })),
    sections: sections.map((s) => ({
        id: s.id,
        name: s.name ?? "",
        text: s.text ?? "",
        uml_class: s.class || null,
        allow_create: !!s.operations?.create,
        allow_update: !!s.operations?.update,
        allow_delete: !!s.operations?.delete,
        attributes: (s.attributes ?? [])
            .map((a: any) => a?.id)
            .filter(Boolean),
    })),
    pages: pages.map((p) => ({
        id: p.id,
        name: p.name ?? "",
        type: p.type?.value ?? "normal",
        category: p.category?.value?.id ?? null,
        action: p.action?.value ?? null,
        sections: (p.sections ?? []).map((s: any) => s.value),
    })),
});

// And back: InterfaceRead into the shapes the editor tabs expect
export const contentToEditor = (
    data: InterfaceRead,
    attributesById: Record<string, any>,
    actionNames: Record<string, string>,
) => {
    const categories = data.categories.map((c) => ({ id: c.id, name: c.name }));

    const sections = data.sections.map((s) => ({
        id: s.id,
        name: s.name,
        text: s.text ?? "",
        class: s.uml_class ?? "",
        operations: {
            create: s.allow_create,
            update: s.allow_update,
            delete: s.allow_delete,
        },
        attributes: s.attributes
            .map((sa) => attributesById[sa.attribute])
            .filter(Boolean),
    }));

    const pages = data.pages.map((p) => {
        const category = categories.find((c) => c.id === p.category);

        return {
            id: p.id,
            name: p.name,
            type: {
                label: p.type === "activity" ? "Activity" : "Normal",
                value: p.type,
            },
            category: category ? { label: category.name, value: category } : null,
            action: p.action
                ? { label: actionNames[p.action] ?? "", value: p.action }
                : null,
            sections: p.page_sections.map((ps) => ({
                label: sections.find((s) => s.id === ps.section)?.name ?? "",
                value: ps.section,
            })),
        };
    });

    return { categories, sections, pages };
};