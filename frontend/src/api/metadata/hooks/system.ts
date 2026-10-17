
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { queryKeys } from "../../querykeys";

import {
    getSystem,
    createSystem,
    updateSystem,
    deleteSystem,
} from "../system";

import type { SystemUpdate } from "../system";

export const useSystem = (systemId: string) => {
    return useQuery({
        queryKey: queryKeys.systems.detail(systemId),
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
                queryKey: queryKeys.projects.detail(system.project),
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

        onSuccess: (_, { systemId }) => {
            queryClient.invalidateQueries({
                queryKey: queryKeys.systems.detail(systemId),
            });

            queryClient.invalidateQueries({
                queryKey: queryKeys.projects.all,
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
        }) => deleteSystem(systemId),

        onSuccess: (_, { systemId }) => {
            queryClient.removeQueries({
                queryKey: queryKeys.systems.detail(systemId),
                exact: true,
            });

            queryClient.invalidateQueries();
        },
    });
};
