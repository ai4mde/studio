import { authAxios } from "$auth/state/auth";
import { useQuery } from "@tanstack/react-query";

// TODO(api): the releases app isn't part of the new backend yet, so none of the
// release calls (here and in ShowReleases) have a replacement for now
// Maarten is working on it 

export type Release = {
    id: string;
    name: string;
    created_at: string;
    release_notes: string[]; 
}

export const useProjectReleases = (projectId: string) => {
    const queryResult = useQuery<Release[]>({
        queryKey: ["project", projectId, "releases"],
        queryFn: async () => {
            const response = await authAxios.get(
                `/v1/metadata/releases/project/${projectId}/`
            );
            return response.data;
        },
        enabled: !!projectId,
    });

    const releases = queryResult.data || [];

    return [
        releases,
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ] as const;
};