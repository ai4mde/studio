
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
    listProjects,
    getProject,
    createProject,
    updateProject,
    deleteProject,
} from "../project";

import type { ProjectUpdate } from "../project";

export const useProjects = () => {
    return useQuery({
        queryKey: ["projects"],
        queryFn: listProjects,
    });
};

export const useProject = (projectId: string) => {
    return useQuery({
        queryKey: ["project", projectId],
        queryFn: () => getProject(projectId),
        enabled: Boolean(projectId),
    });
};

export const useCreateProject = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: createProject,

        onSuccess: () => {
            queryClient.invalidateQueries({
                queryKey: ["projects"],
            });
        },
    });
};

export const useUpdateProject = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            projectId,
            payload,
        }: {
            projectId: string;
            payload: ProjectUpdate;
        }) => updateProject(projectId, payload),

        onSuccess: (_, { projectId }) => {
            queryClient.invalidateQueries({
                queryKey: ["project", projectId],
            });
            queryClient.invalidateQueries({
                queryKey: ["projects"],
            });
        },
    });
};

export const useDeleteProject = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: deleteProject,

        onSuccess: (_, projectId) => {
            queryClient.removeQueries({
                queryKey: ["project", projectId],
                exact: true,
            });
            queryClient.invalidateQueries({
                queryKey: ["projects"],
            });
        },
    });
};
