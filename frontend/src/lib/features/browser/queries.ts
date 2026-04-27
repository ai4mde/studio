import { authAxios } from "$auth/state/auth";
import { useQuery } from "@tanstack/react-query";

export type SystemOut = {
    id: string;
    name: string;
    description?: string;
    project?: string;
};

type ProjectOut = {
    id: string;
    name: string;
    description?: string;
}

export const useSystems = (projectId?: string) =>
    useQuery<SystemOut[]>({
        queryKey: ["systems", `${projectId}`],
        queryFn: async () => {
            return (
                await authAxios.get(`/v1/metadata/systems/`, {
                    params: {
                        project: projectId,
                    },
                })
            ).data;
        },
        enabled: !!projectId,
    });

export const useSystem = (systemId?: string) =>
    useQuery<SystemOut>({
        queryKey: ["system", `${systemId}`],
        queryFn: async () => {
            return (await authAxios.get(`/v1/metadata/systems/${systemId}/`))
                .data;
        },
        enabled: !!systemId,
    });

export const useProject = (projectId? : string) => 
    useQuery<ProjectOut>({
        queryKey: ["project", `${projectId}`],
        queryFn: async () => {
            return (await authAxios.get(`/v1/metadata/projects/${projectId}`))
                .data;
        },
        enabled: !!projectId,
    });

export type SemanticField = {
    kind: "component.field";
    name: string;
    fieldType: string;
    semanticRole: string;
    derived: boolean;
    associatedEntity: boolean;
};

export type SemanticSection = {
    kind: "region.form" | "region.detail";
    entity: string;
    entityRef: string;
    multiplicity: "one" | "many";
    operations: Record<string, boolean>;
    fields: SemanticField[];
};

export type SemanticPageAst = {
    kind: string;
    name: string;
    activityName?: string;
    sections: SemanticSection[];
};

export type UiIrRegion = {
    id: string;
    type: string;
    span?: number;
    components: Array<{
        id: string;
        type: string;
        bind: string | string[];
        attributes: string[];
        field_policies: Record<string, { mode: string; input_type?: string; validation?: string[] }>;
        operations: Record<string, string>;
    }>;
    ast: unknown[];
};

export type UiIrPage = {
    page_id: string;
    name: string;
    layout?: { type: string; columns: number };
    regions: UiIrRegion[];
};

export type InterfaceOut = {
    id: string;
    name: string;
    description?: string;
    project?: string;
    system?: string;
    actor: string;
    data: {
        styling?: Record<string, unknown>;
        categories?: unknown[];
        pages?: Array<{
            id: string;
            name: string;
            semanticAst?: SemanticPageAst;
            renderAst?: unknown[];
            ast?: unknown[];
            sections?: unknown[];
            action?: { label: string; value: string } | null;
        }>;
        sections?: Array<{
            id: string;
            name: string;
            class: string;
            attributes: Array<{
                name: string;
                type: string;
                derived: boolean;
                enum?: unknown;
                semantic_role: string;
                associated_entity: boolean;
                description?: string;
            }>;
            operations: Record<string, boolean>;
        }>;
        settings?: Record<string, unknown>;
        theme?: {
            name?: string;
            description?: string;
            tokens?: Record<string, string>;
        } | null;
        designerSession?: unknown;
        designerMeta?: unknown;
        uiIr?: { pages: UiIrPage[] };
    };
};

export const useInterfaces = (systemId?: string) =>
    useQuery<InterfaceOut[]>({
        queryKey: ["interfaces", `${systemId}`],
        queryFn: async () => {
            return (
                await authAxios.get(`/v1/metadata/interfaces/`, {
                    params: {
                        system: systemId,
                    },
                })
            ).data;
        },
        enabled: !!systemId,
    });

export const useInterface = (interfaceId?: string) =>
    useQuery<InterfaceOut>({
        queryKey: ["interface", `${interfaceId}`],
        queryFn: async () => {
            return (await authAxios.get(`/v1/metadata/interfaces/${interfaceId}/`))
                .data;
        },
        enabled: !!interfaceId,
    });

