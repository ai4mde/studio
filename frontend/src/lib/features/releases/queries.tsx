import { authAxios } from "$auth/state/auth";
import { useQuery } from "@tanstack/react-query";


type Release = {
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