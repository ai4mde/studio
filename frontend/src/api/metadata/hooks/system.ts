
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
    getSystem,
    createSystem,
    updateSystem,
    deleteSystem,
} from "../system";

import type { SystemUpdate } from "../system";

export const useSystem = (systemId: string) => {
    return useQuery({
        queryKey: ["system", systemId],
        queryFn: () => getSystem(systemId),
        enabled: Boolean(systemId),
    });
};

export const useCreateSystem = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: createSystem,

        onSuccess: (system) => {
            queryClient.invalidateQueries({
                queryKey: ["project", system.project],
            });
        },
    });
};

export const useUpdateSystem = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            systemId,
            payload,
        }: {
            systemId: string;
            payload: SystemUpdate;
        }) => updateSystem(systemId, payload),

        onSuccess: (system, { systemId }) => {
            queryClient.invalidateQueries({
                queryKey: ["system", systemId],
            });
            queryClient.invalidateQueries({
                queryKey: ["project", system.project],
            });
        },
    });
};

export const useDeleteSystem = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            systemId,
        }: {
            systemId: string;
            projectId: string;
        }) => deleteSystem(systemId),

        onSuccess: (_, { systemId, projectId }) => {
            queryClient.removeQueries({
                queryKey: ["system", systemId],
                exact: true,
            });
            queryClient.invalidateQueries({
                queryKey: ["project", projectId],
            });
        },
    });
};
