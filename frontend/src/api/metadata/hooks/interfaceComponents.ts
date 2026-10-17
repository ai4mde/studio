
import {
    useMutation,
    useQueryClient,
    type QueryClient,
} from "@tanstack/react-query";

import { queryKeys } from "../../querykeys";

import {
    createPage,
    updatePage,
    deletePage,
    createCategory,
    updateCategory,
    deleteCategory,
    createSection,
    updateSection,
    deleteSection,
    createPageSection,
    updatePageSection,
    deletePageSection,
    createSectionAttribute,
    updateSectionAttribute,
    deleteSectionAttribute,
} from "../interfaceComponents";

import type {
    PageCreate,
    PageUpdate,
    CategoryCreate,
    CategoryUpdate,
    SectionComponentCreate,
    SectionComponentUpdate,
    PageSectionCreate,
    PageSectionUpdate,
    SectionAttributeCreate,
    SectionAttributeUpdate,
} from "../interfaceComponents";

// Invalidate the parent interface after modifying its components.
const invalidateInterface = (
    queryClient: QueryClient,
    interfaceId: string,
) => {
    return queryClient.invalidateQueries({
        queryKey: queryKeys.interfaces.detail(interfaceId),
    });
};

// ============================================================
// Pages
// ============================================================
export const useCreatePage = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            payload,
        }: {
            interfaceId: string;
            payload: PageCreate;
        }) => createPage(payload),

        onSuccess: (_, { interfaceId }) =>
            invalidateInterface(queryClient, interfaceId),
    });
};

export const useUpdatePage = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            pageId,
            payload,
        }: {
            pageId: string;
            interfaceId: string;
            payload: PageUpdate;
        }) => updatePage(pageId, payload),

        onSuccess: (_, { interfaceId }) =>
            invalidateInterface(queryClient, interfaceId),
    });
};

export const useDeletePage = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            pageId,
        }: {
            pageId: string;
            interfaceId: string;
        }) => deletePage(pageId),

        onSuccess: (_, { interfaceId }) =>
            invalidateInterface(queryClient, interfaceId),
    });
};

// ============================================================
// Categories
// ============================================================
export const useCreateCategory = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            payload,
        }: {
            interfaceId: string;
            payload: CategoryCreate;
        }) => createCategory(payload),

        onSuccess: (_, { interfaceId }) =>
            invalidateInterface(queryClient, interfaceId),
    });
};

export const useUpdateCategory = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            categoryId,
            payload,
        }: {
            categoryId: string;
            interfaceId: string;
            payload: CategoryUpdate;
        }) => updateCategory(categoryId, payload),

        onSuccess: (_, { interfaceId }) =>
            invalidateInterface(queryClient, interfaceId),
    });
};

export const useDeleteCategory = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            categoryId,
        }: {
            categoryId: string;
            interfaceId: string;
        }) => deleteCategory(categoryId),

        onSuccess: (_, { interfaceId }) =>
            invalidateInterface(queryClient, interfaceId),
    });
};

// ============================================================
// Sections
// ============================================================
export const useCreateSection = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            payload,
        }: {
            interfaceId: string;
            payload: SectionComponentCreate;
        }) => createSection(payload),

        onSuccess: (_, { interfaceId }) =>
            invalidateInterface(queryClient, interfaceId),
    });
};

export const useUpdateSection = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            sectionId,
            payload,
        }: {
            sectionId: string;
            interfaceId: string;
            payload: SectionComponentUpdate;
        }) => updateSection(sectionId, payload),

        onSuccess: (_, { interfaceId }) =>
            invalidateInterface(queryClient, interfaceId),
    });
};

export const useDeleteSection = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            sectionId,
        }: {
            sectionId: string;
            interfaceId: string;
        }) => deleteSection(sectionId),

        onSuccess: (_, { interfaceId }) =>
            invalidateInterface(queryClient, interfaceId),
    });
};

// ============================================================
// Page Sections
// ============================================================
export const useCreatePageSection = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            payload,
        }: {
            interfaceId: string;
            payload: PageSectionCreate;
        }) => createPageSection(payload),

        onSuccess: (_, { interfaceId }) =>
            invalidateInterface(queryClient, interfaceId),
    });
};

export const useUpdatePageSection = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            pageSectionId,
            payload,
        }: {
            pageSectionId: string;
            interfaceId: string;
            payload: PageSectionUpdate;
        }) => updatePageSection(pageSectionId, payload),

        onSuccess: (_, { interfaceId }) =>
            invalidateInterface(queryClient, interfaceId),
    });
};

export const useDeletePageSection = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            pageSectionId,
        }: {
            pageSectionId: string;
            interfaceId: string;
        }) => deletePageSection(pageSectionId),

        onSuccess: (_, { interfaceId }) =>
            invalidateInterface(queryClient, interfaceId),
    });
};

// ============================================================
// Section Attributes
// ============================================================
export const useCreateSectionAttribute = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            payload,
        }: {
            interfaceId: string;
            payload: SectionAttributeCreate;
        }) => createSectionAttribute(payload),

        onSuccess: (_, { interfaceId }) =>
            invalidateInterface(queryClient, interfaceId),
    });
};

export const useUpdateSectionAttribute = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            sectionAttributeId,
            payload,
        }: {
            sectionAttributeId: string;
            interfaceId: string;
            payload: SectionAttributeUpdate;
        }) => updateSectionAttribute(sectionAttributeId, payload),

        onSuccess: (_, { interfaceId }) =>
            invalidateInterface(queryClient, interfaceId),
    });
};

export const useDeleteSectionAttribute = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            sectionAttributeId,
        }: {
            sectionAttributeId: string;
            interfaceId: string;
        }) => deleteSectionAttribute(sectionAttributeId),

        onSuccess: (_, { interfaceId }) =>
            invalidateInterface(queryClient, interfaceId),
    });
};
