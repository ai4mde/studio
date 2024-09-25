import { useQuery } from "@tanstack/react-query";
import { authAxios } from "../auth/state/auth";

export const useSystemMetadata = (systemId: string) =>
    useQuery({
        queryKey: ["system", "metadata", `${systemId}`],
        queryFn: async () => {
            const response = await authAxios.get(
                `/v1/metadata/systems/${systemId}/meta/`,
            );
            return response.data;
        },
    });


export const useActor = (systemId: string, classifierId: string) => {
    if (!classifierId) {
        return "";
    }
    const queryResult = useQuery({
        queryKey: ["system", "metadata", systemId, "classifiers", classifierId],
        queryFn: async () => {
            const response = await authAxios.get(`/v1/metadata/systems/${systemId}/classifiers/${classifierId}`);
            return response.data;
        },
    });

    const actor = queryResult.data?.data.name;

    return [
        actor,
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ];
};