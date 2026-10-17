
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { queryKeys } from "../../querykeys";

import {
    createEdge,
    updateEdge,
    deleteEdge,
} from "../edge";

import type { EdgeCreate, EdgeUpdate } from "../edge";

export const useCreateEdge = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            diagramId,
            payload,
        }: {
            diagramId: string;
            payload: EdgeCreate;
        }) => createEdge(diagramId, payload),

        onSuccess: (_, { diagramId }) => {
            queryClient.invalidateQueries({
                queryKey: queryKeys.diagrams.detail(diagramId),
            });
        },
    });
};

export const useUpdateEdge = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            edgeId,
            payload,
        }: {
            edgeId: string;
            diagramId: string;
            payload: EdgeUpdate;
        }) => updateEdge(edgeId, payload),

        onSuccess: (_, { diagramId }) => {
            queryClient.invalidateQueries({
                queryKey: queryKeys.diagrams.detail(diagramId),
            });
        },
    });
};

export const useDeleteEdge = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            edgeId,
        }: {
            edgeId: string;
            diagramId: string;
        }) => deleteEdge(edgeId),

        onSuccess: (_, { diagramId }) => {
            queryClient.invalidateQueries({
                queryKey: queryKeys.diagrams.detail(diagramId),
            });
        },
    });
};
