
import { apiClient } from "../client";
import type { components, operations } from "../generated/schema";

type ListInterfaces = operations["metadata_api_routes_interface_list_interfaces"];

export type InterfaceSummary = components["schemas"]["InterfaceSummary"];
export type InterfaceRead = components["schemas"]["InterfaceRead"];
export type InterfaceCreate = components["schemas"]["InterfaceCreate"];
export type InterfaceUpdate = components["schemas"]["InterfaceUpdate"];
export type InterfaceFilters = NonNullable<ListInterfaces["parameters"]["query"]>;


export async function listInterfaces(
    filters: InterfaceFilters = {}
): Promise<InterfaceSummary[]> {
    const { data } = await apiClient.get<InterfaceSummary[]>(
        "/v1/metadata/interfaces/",
        { params: filters }
    );

    return data;
}

export async function getInterface(
    interfaceId: string
): Promise<InterfaceRead> {
    const { data } = await apiClient.get<InterfaceRead>(
        `/v1/metadata/interfaces/${interfaceId}/`
    );

    return data;
}

export async function createInterface(
    payload: InterfaceCreate
): Promise<InterfaceRead> {
    const { data } = await apiClient.post<InterfaceRead>(
        "/v1/metadata/interfaces/",
        payload
    );

    return data;
}

export async function updateInterface(
    interfaceId: string,
    payload: InterfaceUpdate
): Promise<InterfaceRead> {
    const { data } = await apiClient.patch<InterfaceRead>(
        `/v1/metadata/interfaces/${interfaceId}/`,
        payload
    );

    return data;
}

export async function deleteInterface(
    interfaceId: string
): Promise<void> {
    await apiClient.delete(
        `/v1/metadata/interfaces/${interfaceId}/`
    );
}
