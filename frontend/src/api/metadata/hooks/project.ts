
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { queryKeys } from "../../querykeys";

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
        queryKey: queryKeys.projects.list(),
        queryFn: listProjects,
    });
};

export const useProject = (projectId: string) => {
    return useQuery({
        queryKey: queryKeys.projects.detail(projectId),
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
                queryKey: queryKeys.projects.list(),
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
                queryKey: queryKeys.projects.detail(projectId),
            });

            queryClient.invalidateQueries({
                queryKey: queryKeys.projects.list(),
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
                queryKey: queryKeys.projects.detail(projectId),
                exact: true,
            });

            queryClient.invalidateQueries();
        },
    });
};
