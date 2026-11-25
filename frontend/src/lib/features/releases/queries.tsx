import { useQuery } from "@tanstack/react-query";
import { listReleases } from "../../../api/metadata/releases";

export type Release = {
    id: string;
    name: string;
    created_at: string;
    release_notes: string[];
};

export const useProjectReleases = (projectId: string) => {
    const queryResult = useQuery<Release[]>({
        queryKey: ["project", projectId, "releases"],
        queryFn: async () =>
            (await listReleases(projectId)) as unknown as Release[],
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
