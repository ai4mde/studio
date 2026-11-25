import { apiClient } from "../client";
import type { components } from "../generated/schema";

export type AttributeRead = components["schemas"]["AttributeRead"];
export type AttributeCreate = components["schemas"]["AttributeCreate"];
export type AttributeUpdate = components["schemas"]["AttributeUpdate"];
export type OperationRead = components["schemas"]["OperationRead"];
export type OperationCreate = components["schemas"]["OperationCreate"];
export type OperationUpdate = components["schemas"]["OperationUpdate"];

// ============================================================
// Attributes
// ============================================================
export async function listAttributes(classifierId: string): Promise<AttributeRead[]> {
    const { data } = await apiClient.get<AttributeRead[]>(
        `/v1/metadata/classifiers/${classifierId}/attributes/`
    );
    return data;
}

export async function createAttribute(
    classifierId: string,
    payload: AttributeCreate
): Promise<AttributeRead> {
    const { data } = await apiClient.post<AttributeRead>(
        `/v1/metadata/classifiers/${classifierId}/attributes/`,
        payload
    );
    return data;
}

export async function updateAttribute(
    attributeId: string,
    payload: AttributeUpdate
): Promise<AttributeRead> {
    const { data } = await apiClient.patch<AttributeRead>(
        `/v1/metadata/classifiers/attributes/${attributeId}/`,
        payload
    );
    return data;
}

export async function deleteAttribute(attributeId: string): Promise<void> {
    await apiClient.delete(`/v1/metadata/classifiers/attributes/${attributeId}/`);
}

// ============================================================
// Operations
// ============================================================
export async function listOperations(classifierId: string): Promise<OperationRead[]> {
    const { data } = await apiClient.get<OperationRead[]>(
        `/v1/metadata/classifiers/${classifierId}/operations/`
    );
    return data;
}

export async function createOperation(
    classifierId: string,
    payload: OperationCreate
): Promise<OperationRead> {
    const { data } = await apiClient.post<OperationRead>(
        `/v1/metadata/classifiers/${classifierId}/operations/`,
        payload
    );
    return data;
}

export async function updateOperation(
    operationId: string,
    payload: OperationUpdate
): Promise<OperationRead> {
    const { data } = await apiClient.patch<OperationRead>(
        `/v1/metadata/classifiers/operations/${operationId}/`,
        payload
    );
    return data;
}

export async function deleteOperation(operationId: string): Promise<void> {
    await apiClient.delete(`/v1/metadata/classifiers/operations/${operationId}/`);
}