
import type { ClassifierFilters } from "./metadata/classifier";
import type { InterfaceFilters } from "./metadata/interface";

export const queryKeys = {
    projects: {
        all: ["projects"] as const,
        list: () => ["projects", "list"] as const,
        detail: (projectId: string) =>
            ["projects", "detail", projectId] as const,
    },

    systems: {
        all: ["systems"] as const,
        detail: (systemId: string) =>
            ["systems", "detail", systemId] as const,
    },

    diagrams: {
        all: ["diagrams"] as const,
        lists: () => ["diagrams", "list"] as const,
        list: (systemId: string) =>
            ["diagrams", "list", systemId] as const,
        detail: (diagramId: string) =>
            ["diagrams", "detail", diagramId] as const,
    },

    classifiers: {
        all: ["classifiers"] as const,
        lists: () => ["classifiers", "list"] as const,
        list: (filters: ClassifierFilters = {}) =>
            ["classifiers", "list", filters] as const,
    },
    interfaces: {
    all: ["interfaces"] as const,
    lists: () => ["interfaces", "list"] as const,
    list: (filters: InterfaceFilters = {}) =>
        ["interfaces", "list", filters] as const,
    detail: (interfaceId: string) =>
        ["interfaces", "detail", interfaceId] as const,
},
};
