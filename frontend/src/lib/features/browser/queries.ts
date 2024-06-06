import { authAxios } from "$auth/state/auth";
import { useQuery } from "@tanstack/react-query";

export type SystemOut = {
    id: string;
    name: string;
    description?: string;
    project?: string;
};

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
