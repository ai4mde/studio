
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

export function classifierNameExists(
    classifiers: ClassifierRead[],
    name: string,
    type: ClassifierRead["type"],
    excludeId?: string,
): boolean {
    const normalizedName = name.trim().toLowerCase();

    if (!normalizedName) return false;

    return classifiers.some((classifier) => {
        if (classifier.id === excludeId || classifier.type !== type) {
            return false;
        }

        if (!("name" in classifier.data)) {
            return false;
        }

        return (
            typeof classifier.data.name === "string" &&
            classifier.data.name.trim().toLowerCase() === normalizedName
        );
    });
}
