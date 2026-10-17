
import { apiClient } from "../client";
import type { components } from "../generated/schema";

// ============================================================
// Pages
// ============================================================
export type PageRead = components["schemas"]["PageRead"];
export type PageCreate = components["schemas"]["PageCreate"];
export type PageUpdate = components["schemas"]["PageUpdate"];

export async function createPage(
    payload: PageCreate
): Promise<PageRead> {
    const { data } = await apiClient.post<PageRead>(
        "/v1/metadata/interfaces/pages/",
        payload
    );

    return data;
}

export async function updatePage(
    pageId: string,
    payload: PageUpdate
): Promise<PageRead> {
    const { data } = await apiClient.patch<PageRead>(
        `/v1/metadata/interfaces/pages/${pageId}/`,
        payload
    );

    return data;
}

export async function deletePage(
    pageId: string
): Promise<void> {
    await apiClient.delete(
        `/v1/metadata/interfaces/pages/${pageId}/`
    );
}

// ============================================================
// Categories
// ============================================================
export type CategoryRead = components["schemas"]["CategoryRead"];
export type CategoryCreate = components["schemas"]["CategoryCreate"];
export type CategoryUpdate = components["schemas"]["CategoryUpdate"];

export async function createCategory(
    payload: CategoryCreate
): Promise<CategoryRead> {
    const { data } = await apiClient.post<CategoryRead>(
        "/v1/metadata/interfaces/categories/",
        payload
    );

    return data;
}

export async function updateCategory(
    categoryId: string,
    payload: CategoryUpdate
): Promise<CategoryRead> {
    const { data } = await apiClient.patch<CategoryRead>(
        `/v1/metadata/interfaces/categories/${categoryId}/`,
        payload
    );

    return data;
}

export async function deleteCategory(
    categoryId: string
): Promise<void> {
    await apiClient.delete(
        `/v1/metadata/interfaces/categories/${categoryId}/`
    );
}

// ============================================================
// Sections
// ============================================================
export type SectionComponentRead = components["schemas"]["SectionComponentRead"];
export type SectionComponentCreate = components["schemas"]["SectionComponentCreate"];
export type SectionComponentUpdate = components["schemas"]["SectionComponentUpdate"];

export async function createSection(
    payload: SectionComponentCreate
): Promise<SectionComponentRead> {
    const { data } = await apiClient.post<SectionComponentRead>(
        "/v1/metadata/interfaces/sections/",
        payload
    );

    return data;
}

export async function updateSection(
    sectionId: string,
    payload: SectionComponentUpdate
): Promise<SectionComponentRead> {
    const { data } = await apiClient.patch<SectionComponentRead>(
        `/v1/metadata/interfaces/sections/${sectionId}/`,
        payload
    );

    return data;
}

export async function deleteSection(
    sectionId: string
): Promise<void> {
    await apiClient.delete(
        `/v1/metadata/interfaces/sections/${sectionId}/`
    );
}

// ============================================================
// Page Sections
// ============================================================
export type PageSectionRead = components["schemas"]["PageSectionRead"];
export type PageSectionCreate = components["schemas"]["PageSectionCreate"];
export type PageSectionUpdate = components["schemas"]["PageSectionUpdate"];

export async function createPageSection(
    payload: PageSectionCreate
): Promise<PageSectionRead> {
    const { data } = await apiClient.post<PageSectionRead>(
        "/v1/metadata/interfaces/page-sections/",
        payload
    );

    return data;
}

export async function updatePageSection(
    pageSectionId: string,
    payload: PageSectionUpdate
): Promise<PageSectionRead> {
    const { data } = await apiClient.patch<PageSectionRead>(
        `/v1/metadata/interfaces/page-sections/${pageSectionId}/`,
        payload
    );

    return data;
}

export async function deletePageSection(
    pageSectionId: string
): Promise<void> {
    await apiClient.delete(
        `/v1/metadata/interfaces/page-sections/${pageSectionId}/`
    );
}

// ============================================================
// Section Attributes
// ============================================================
export type SectionAttributeRead = components["schemas"]["SectionAttributeRead"];
export type SectionAttributeCreate = components["schemas"]["SectionAttributeCreate"];
export type SectionAttributeUpdate = components["schemas"]["SectionAttributeUpdate"];

export async function createSectionAttribute(
    payload: SectionAttributeCreate
): Promise<SectionAttributeRead> {
    const { data } = await apiClient.post<SectionAttributeRead>(
        "/v1/metadata/interfaces/section-attributes/",
        payload
    );

    return data;
}

export async function updateSectionAttribute(
    sectionAttributeId: string,
    payload: SectionAttributeUpdate
): Promise<SectionAttributeRead> {
    const { data } = await apiClient.patch<SectionAttributeRead>(
        `/v1/metadata/interfaces/section-attributes/${sectionAttributeId}/`,
        payload
    );

    return data;
}

export async function deleteSectionAttribute(
    sectionAttributeId: string
): Promise<void> {
    await apiClient.delete(
        `/v1/metadata/interfaces/section-attributes/${sectionAttributeId}/`
    );
}
