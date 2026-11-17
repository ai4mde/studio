import { apiClient } from "../client";
import type { components } from "../generated/schema";

export type ProjectRead = components["schemas"]["ProjectRead"];
export type ProjectCreate = components["schemas"]["ProjectCreate"];
export type ProjectUpdate = components["schemas"]["ProjectUpdate"];
export type ProjectList = components["schemas"]["ProjectList"];

export async function listProjects(): Promise<ProjectList[]> {
    const { data } = await apiClient.get<ProjectList[]>(
        "/v1/metadata/projects/"
    );
    return data;
}

export async function getProject(
    projectId: string
): Promise<ProjectRead> {
    const { data } = await apiClient.get<ProjectRead>(
        `/v1/metadata/projects/${projectId}/`
    );
    return data;
}

export async function createProject(
    payload: ProjectCreate
): Promise<ProjectRead> {
    const { data } = await apiClient.post<ProjectRead>(
        "/v1/metadata/projects/",
        payload
    );
    return data;
}

export async function updateProject(
    projectId: string,
    payload: ProjectUpdate
): Promise<ProjectRead> {
    const { data } = await apiClient.patch<ProjectRead>(
        `/v1/metadata/projects/${projectId}/`,
        payload
    );
    return data;
}

export async function deleteProject(
    projectId: string
): Promise<void> {
    await apiClient.delete(
        `/v1/metadata/projects/${projectId}/`
    );
}

// Upload a project file (a release export); the backend recreates the project
export async function importProject(file: File): Promise<ProjectRead> {
    const formData = new FormData();
    formData.append("file", file);

    const { data } = await apiClient.post<ProjectRead>(
        "/v1/metadata/projects/import/",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
    );
    return data;
}
// The current state of a project, in the same format as a release export
export async function exportProject(projectId: string): Promise<unknown> {
    const { data } = await apiClient.get(`/v1/metadata/projects/${projectId}/export/`);
    return data;
}

// Selected systems of a project, to import into a project later
export async function exportProjectSystems(
    projectId: string,
    systemIds: string[]
): Promise<unknown> {
    const { data } = await apiClient.get(
        `/v1/metadata/projects/${projectId}/systems/export/`,
        {
            params: { system_ids: systemIds },
            // system_ids=a&system_ids=b, not system_ids[]=a
            paramsSerializer: { indexes: null },
        }
    );
    return data;
}
