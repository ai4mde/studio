import { authAxios } from "$auth/state/auth";
import { useQuery } from "@tanstack/react-query";
import { getProject } from "$lib/endpoints/projects";
import type { ProjectOut } from "$lib/types/projects";
import { getSystems, getSystem } from "$lib/endpoints/systems";
import type { SystemOut } from "$lib/types/systems";

export const useSystems = (projectId?: string) =>
    useQuery<SystemOut[]>({
        queryKey: ["systems", `${projectId}`],
        queryFn: () => getSystems(projectId!),
        enabled: !!projectId,
    });

export const useSystem = (systemId?: string) =>
    useQuery<SystemOut>({
        queryKey: ["system", `${systemId}`],
        queryFn: () => getSystem(systemId!),
        enabled: !!systemId,
    });

export const useProject = (projectId?: string) =>
    useQuery<ProjectOut>({
        queryKey: ["project", `${projectId}`],
        queryFn: () => getProject(projectId!),
        enabled: !!projectId,
    });

export type InterfaceOut = {
    id: string;
    name: string;
    description?: string;
    project?: string;
    system?: string;
    actor: string;
    data: string;
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

