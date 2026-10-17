
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
    getDiagram,
    listDiagrams,
    createDiagram,
    updateDiagram,
    deleteDiagram,
} from "../diagram";

import type { DiagramUpdate } from "../diagram";

// Queries

export const useDiagram = (diagramId: string) => {
    return useQuery({
        queryKey: ["diagram", diagramId],
        queryFn: () => getDiagram(diagramId),
        enabled: Boolean(diagramId),
    });
};

export const useDiagrams = (systemId: string) => {
    return useQuery({
        queryKey: ["diagrams", systemId],
        queryFn: () => listDiagrams(systemId),
        enabled: Boolean(systemId),
    });
};

// Mutations

export const useCreateDiagram = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: createDiagram,
        onSuccess: () => {
            queryClient.invalidateQueries({
                queryKey: ["diagrams"],
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
                queryKey: ["diagram", diagramId],
            });
            queryClient.invalidateQueries({
                queryKey: ["diagrams"],
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
                queryKey: ["diagram", diagramId],
                exact: true,
            });
            queryClient.invalidateQueries({
                queryKey: ["diagrams"],
            });
        },
    });
};
