
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { queryKeys } from "../../querykeys";

import {
    getDiagram,
    listDiagrams,
    createDiagram,
    updateDiagram,
    deleteDiagram,
} from "../diagram";

import type { DiagramUpdate } from "../diagram";

export const useDiagram = (diagramId: string) => {
    return useQuery({
        queryKey: queryKeys.diagrams.detail(diagramId),
        queryFn: () => getDiagram(diagramId),
        enabled: Boolean(diagramId),
    });
};

export const useDiagrams = (systemId: string) => {
    return useQuery({
        queryKey: queryKeys.diagrams.list(systemId),
        queryFn: () => listDiagrams(systemId),
        enabled: Boolean(systemId),
    });
};

export const useCreateDiagram = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: createDiagram,

        onSuccess: (diagram) => {
            queryClient.invalidateQueries({
                queryKey: queryKeys.diagrams.list(diagram.system),
            });
        },
    });
};

export const useUpdateDiagram = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            diagramId,
            payload,
        }: {
            diagramId: string;
            payload: DiagramUpdate;
        }) => updateDiagram(diagramId, payload),

        onSuccess: (_, { diagramId }) => {
            queryClient.invalidateQueries({
                queryKey: queryKeys.diagrams.detail(diagramId),
            });

            queryClient.invalidateQueries({
                queryKey: queryKeys.diagrams.lists(),
            });
        },
    });
};

export const useDeleteDiagram = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: deleteDiagram,

        onSuccess: (_, diagramId) => {
            queryClient.removeQueries({
                queryKey: queryKeys.diagrams.detail(diagramId),
                exact: true,
            });

            queryClient.invalidateQueries();
        },
    });
};
