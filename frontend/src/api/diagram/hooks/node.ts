
import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
    createNode,
    updateNode,
    deleteNode,
} from "../node";

import type { NodeCreate, NodeUpdate } from "../node";

// Create node

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
                queryKey: ["diagram", diagramId],
            });
            queryClient.invalidateQueries({
                queryKey: ["classifiers"],
            });
        },
    });
};

// Update node

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
                queryKey: ["diagram", diagramId],
            });

            if (payload.classifier != null) {
                queryClient.invalidateQueries({
                    queryKey: ["classifiers"],
                });
            }
        },
    });
};

// Delete node

export const useDeleteNode = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            nodeId,
        }: {
            nodeId: string;
            diagramId: string;
        }) => deleteNode(nodeId),

        onSuccess: (_, { diagramId }) => {
            queryClient.invalidateQueries({
                queryKey: ["diagram", diagramId],
            });
            queryClient.invalidateQueries({
                queryKey: ["classifiers"],
            });
        },
    });
};
