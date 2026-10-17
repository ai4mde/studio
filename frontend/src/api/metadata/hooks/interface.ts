
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { queryKeys } from "../../querykeys";

import {
    listInterfaces,
    getInterface,
    createInterface,
    updateInterface,
    deleteInterface,
} from "../interface";

import type { InterfaceFilters, InterfaceUpdate } from "../interface";

export const useInterfaces = (filters: InterfaceFilters = {}) => {
    return useQuery({
        queryKey: queryKeys.interfaces.list(filters),
        queryFn: () => listInterfaces(filters),
    });
};

export const useInterface = (interfaceId: string) => {
    return useQuery({
        queryKey: queryKeys.interfaces.detail(interfaceId),
        queryFn: () => getInterface(interfaceId),
        enabled: Boolean(interfaceId),
    });
};

export const useCreateInterface = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: createInterface,

        onSuccess: () => {
            queryClient.invalidateQueries({
                queryKey: queryKeys.interfaces.lists(),
            });
        },
    });
};

export const useUpdateInterface = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            interfaceId,
            payload,
        }: {
            interfaceId: string;
            payload: InterfaceUpdate;
        }) => updateInterface(interfaceId, payload),

        onSuccess: (_, { interfaceId }) => {
            queryClient.invalidateQueries({
                queryKey: queryKeys.interfaces.detail(interfaceId),
            });

            queryClient.invalidateQueries({
                queryKey: queryKeys.interfaces.lists(),
            });
        },
    });
};

export const useDeleteInterface = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: deleteInterface,

        onSuccess: (_, interfaceId) => {
            queryClient.removeQueries({
                queryKey: queryKeys.interfaces.detail(interfaceId),
                exact: true,
            });

            queryClient.invalidateQueries();
        },
    });
};
