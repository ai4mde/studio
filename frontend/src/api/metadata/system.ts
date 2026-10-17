
import { apiClient } from "../client";
import type { components } from "../generated/schema";

export type SystemRead = components["schemas"]["SystemRead"];
export type SystemCreate = components["schemas"]["SystemCreate"];
export type SystemUpdate = components["schemas"]["SystemUpdate"];


export async function getSystem(
    systemId: string
): Promise<SystemRead> {
    const { data } = await apiClient.get<SystemRead>(
        `/v1/metadata/systems/${systemId}/`
    );
    return data;
}

export async function createSystem(
    payload: SystemCreate
): Promise<SystemRead> {
    const { data } = await apiClient.post<SystemRead>(
        "/v1/metadata/systems/",
        payload
    );
    return data;
}

export async function updateSystem(
    systemId: string,
    payload: SystemUpdate
): Promise<SystemRead> {
    const { data } = await apiClient.patch<SystemRead>(
        `/v1/metadata/systems/${systemId}/`,
        payload
    );
    return data;
}

export async function deleteSystem(
    systemId: string
): Promise<void> {
    await apiClient.delete(
        `/v1/metadata/systems/${systemId}/`
    );
}
