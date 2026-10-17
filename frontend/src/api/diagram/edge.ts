
import { apiClient } from "../client";
import type { components } from "../generated/schema";

export type EdgeCreate = components["schemas"]["EdgeCreate"];
export type EdgeUpdate = components["schemas"]["EdgeUpdate"];
export type EdgeRead = components["schemas"]["EdgeRead"];

export async function createEdge(
    diagramId: string,
    payload: EdgeCreate
): Promise<EdgeRead> {
    const { data } = await apiClient.post<EdgeRead>(
        `/v1/diagram/${diagramId}/edge/`,
        payload
    );
    return data;
}

export async function updateEdge(
    edgeId: string,
    payload: EdgeUpdate
): Promise<EdgeRead> {
    const { data } = await apiClient.patch<EdgeRead>(
        `/v1/diagram/edge/${edgeId}/`,
        payload
    );
    return data;
}

export async function deleteEdge(
    edgeId: string
): Promise<void> {
    await apiClient.delete(
        `/v1/diagram/edge/${edgeId}/`
    );
}
