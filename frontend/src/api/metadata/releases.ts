import { apiClient } from "../client";
import type { components } from "../generated/schema";

export type ReleaseList = components["schemas"]["ReleaseList"];
export type ReleaseCreate = components["schemas"]["ReleaseCreate"];
type ProjectRead = components["schemas"]["ProjectRead"];

const multipart = { headers: { "Content-Type": "multipart/form-data" } };

export async function listReleases(projectId: string): Promise<ReleaseList[]> {
    const { data } = await apiClient.get<ReleaseList[]>("/v1/metadata/releases/", {
        params: { project_id: projectId },
    });
    return data;
}

export async function createRelease(payload: ReleaseCreate): Promise<ReleaseList> {
    const { data } = await apiClient.post<ReleaseList>("/v1/metadata/releases/", payload);
    return data;
}

export async function deleteRelease(releaseId: string): Promise<void> {
    await apiClient.delete(`/v1/metadata/releases/${releaseId}/`);
}

// The snapshot of the project at that release, as JSON
export async function exportRelease(releaseId: string): Promise<unknown> {
    const { data } = await apiClient.get(`/v1/metadata/releases/${releaseId}/export/`);
    return data;
}

// Upload an exported release (or project) file as a new version of a project
export async function importRelease(
    projectId: string,
    file: File,
    name: string,
    description = ""
): Promise<ReleaseList> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("name", name);
    formData.append("description", description);

    const { data } = await apiClient.post<ReleaseList>(
        `/v1/metadata/releases/import/${projectId}/`,
        formData,
        multipart
    );
    return data;
}

// Add the systems from a systems export to a project, then create a release
export async function importSystemsRelease(
    projectId: string,
    file: File,
    name: string,
    releaseNotes: string[] = []
): Promise<ReleaseList> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("name", name);
    formData.append("release_notes", JSON.stringify(releaseNotes));

    const { data } = await apiClient.post<ReleaseList>(
        `/v1/metadata/releases/import_systems/${projectId}/`,
        formData,
        multipart
    );
    return data;
}

// Replace the project's current content with this release. Without force, the
// backend refuses (409) when the project has changes since its last release.
export async function restoreRelease(
    releaseId: string,
    force = false
): Promise<ProjectRead> {
    const { data } = await apiClient.post<ProjectRead>(
        `/v1/metadata/releases/${releaseId}/restore/`,
        null,
        { params: { force } }
    );
    return data;
}
