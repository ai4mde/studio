
import { apiClient } from "../client";
import type { components } from "../generated/schema";

export type NodeCreate = components["schemas"]["NodeCreate"];
export type NodeUpdate = components["schemas"]["NodeUpdate"];
export type NodeRead = components["schemas"]["NodeRead"];

export async function createNode(
    diagramId: string,
    payload: NodeCreate
): Promise<NodeRead> {
    const { data } = await apiClient.post<NodeRead>(
        `/v1/diagram/${diagramId}/node/`,
        payload
    );
    return data;
}

export async function updateNode(
    nodeId: string,
    payload: NodeUpdate
): Promise<NodeRead> {
    const { data } = await apiClient.patch<NodeRead>(
        `/v1/diagram/node/${nodeId}/`,
        payload
    );
    return data;
}

export async function deleteNode(
    nodeId: string
): Promise<void> {
    await apiClient.delete(
        `/v1/diagram/node/${nodeId}/`
    );
}
