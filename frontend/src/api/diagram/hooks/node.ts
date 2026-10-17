
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { queryKeys } from "../../querykeys";

import {
    createNode,
    updateNode,
    deleteNode,
} from "../node";

import type { NodeCreate, NodeUpdate } from "../node";

export const useCreateNode = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            diagramId,
            payload,
        }: {
            diagramId: string;
            payload: NodeCreate;
        }) => createNode(diagramId, payload),

        onSuccess: (_, { diagramId }) => {
            queryClient.invalidateQueries({
                queryKey: queryKeys.diagrams.detail(diagramId),
            });

            queryClient.invalidateQueries({
                queryKey: queryKeys.classifiers.all,
            });
        },
    });
};

export const useUpdateNode = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            nodeId,
            payload,
        }: {
            nodeId: string;
            diagramId: string;
            payload: NodeUpdate;
        }) => updateNode(nodeId, payload),

        onSuccess: (_, { diagramId, payload }) => {
            queryClient.invalidateQueries({
                queryKey: queryKeys.diagrams.detail(diagramId),
            });

            if (payload.classifier !== undefined) {
                queryClient.invalidateQueries({
                    queryKey: queryKeys.classifiers.all,
                });
            }
        },
    });
};

export const useDeleteNode = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            nodeId,
        }: {
            nodeId: string;
            diagramId: string;
        }) => deleteNode(nodeId),

        onSuccess: () => {
            queryClient.invalidateQueries();
        },
    });
};
