
import { apiClient } from "../client";
import type { components } from "../generated/schema";

export type DiagramRead = components["schemas"]["DiagramRead"];
export type DiagramReadFull = components["schemas"]["DiagramReadFull"];
export type DiagramCreate = components["schemas"]["DiagramCreate"];
export type DiagramUpdate = components["schemas"]["DiagramUpdate"];

export async function listDiagrams(
    systemId: string
): Promise<DiagramRead[]> {
    const { data } = await apiClient.get<DiagramRead[]>(
        "/v1/diagram/",
        { params: { system_id: systemId } }
    );
    return data;
}

export async function getDiagram(
    diagramId: string
): Promise<DiagramReadFull> {
    const { data } = await apiClient.get<DiagramReadFull>(
        `/v1/diagram/${diagramId}/`
    );
    return data;
}

export async function createDiagram(
    payload: DiagramCreate
): Promise<DiagramRead> {
    const { data } = await apiClient.post<DiagramRead>(
        "/v1/diagram/",
        payload
    );
    return data;
}

export async function updateDiagram(
    diagramId: string,
    payload: DiagramUpdate
): Promise<DiagramRead> {
    const { data } = await apiClient.patch<DiagramRead>(
        `/v1/diagram/${diagramId}/`,
        payload
    );
    return data;
}

export async function deleteDiagram(
    diagramId: string
): Promise<void> {
    await apiClient.delete(`/v1/diagram/${diagramId}/`);
}