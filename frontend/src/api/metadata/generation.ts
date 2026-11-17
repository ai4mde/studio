import { apiClient } from "../client";
import type { components } from "../generated/schema";

export type GenerateAttribute = components["schemas"]["GenerateAttribute"];
export type GenerateMethod = components["schemas"]["GenerateMethod"];

// Both return the generated Python code as a string
export async function generateAttribute(
    classifierId: string,
    payload: GenerateAttribute
): Promise<string> {
    const { data } = await apiClient.post<string>(
        `/v1/metadata/generation/${classifierId}/attribute/`,
        payload
    );
    return data;
}

export async function generateMethod(
    classifierId: string,
    payload: GenerateMethod
): Promise<string> {
    const { data } = await apiClient.post<string>(
        `/v1/metadata/generation/${classifierId}/method/`,
        payload
    );
    return data;
}