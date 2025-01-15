import { authAxios } from "$auth/state/auth";
import { useQuery } from "@tanstack/react-query";

export const useSystemReleases = (systemId: string) => {
    const queryResult = useQuery({
        queryKey: ["system", systemId, "releases"],
        queryFn: async () => {
            const response = await authAxios.get(`/v1/metadata/releases/system/${systemId}/`, {
                params: {
                    system: systemId
                }
            });
            return response.data;
        },
    });

    const releases = queryResult.data || [];

    return [
        releases,
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ];
};