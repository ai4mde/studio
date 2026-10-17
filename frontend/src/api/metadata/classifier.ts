
import { apiClient } from "../client";
import type { operations } from "../generated/schema";


type ListClassifiers =
    operations["metadata_api_routes_classifier_list_classifiers"];

export type ClassifierRead =
    ListClassifiers["responses"][200]["content"]["application/json"][number];

export type ClassifierFilters =
    NonNullable<ListClassifiers["parameters"]["query"]>;


export async function listClassifiers(
    filters: ClassifierFilters = {}
): Promise<ClassifierRead[]> {
    const { data } = await apiClient.get<ClassifierRead[]>(
        "/v1/metadata/classifiers/",
        { params: filters }
    );

    return data;
}
