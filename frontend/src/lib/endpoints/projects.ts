import { authAxios } from "$auth/state/auth";
import type {
    ProjectOut,
    ProjectCreate,
    ProjectUpdate,
} from "../types/projects";

export const getProjects = async (): Promise<ProjectOut[]> => {
    const { data } = await authAxios.get<ProjectOut[]>(
        "/v1/metadata/projects/"
    );
    return data;
};

export const getProject = async (
    projectId: string
): Promise<ProjectOut> => {
    const { data } = await authAxios.get<ProjectOut>(
        `/v1/metadata/projects/${projectId}/`
    );
    return data;
};

export const createProject = async (
    payload: ProjectCreate
): Promise<ProjectOut> => {
    const { data } = await authAxios.post<ProjectOut>(
        "/v1/metadata/projects/",
        payload
    );
    return data;
};

export const updateProject = async (
    projectId: string,
    payload: ProjectUpdate
): Promise<ProjectOut> => {
    const { data } = await authAxios.patch<ProjectOut>(
        `/v1/metadata/projects/${projectId}/`,
        payload
    );
    return data;
};

export const deleteProject = async (
    projectId: string
): Promise<void> => {
    await authAxios.delete(
        `/v1/metadata/projects/${projectId}/`
    );
};

export const importProject = async (
    payload: unknown
): Promise<void> => {
    await authAxios.post(
        "/v1/metadata/projects/import/",
        payload
    );
};

export const exportProject = async (
    projectId: string
): Promise<unknown> => {
    const { data } = await authAxios.get(
        `/v1/metadata/projects/export/${projectId}/`
    );

    return data;
};