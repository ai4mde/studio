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
    const hasClassifier = Boolean(classifierId);
    const queryResult = useQuery({
        queryKey: ["system", "metadata", systemId, "classifiers", classifierId],
        queryFn: async () => {
            const response = await authAxios.get(`/v1/metadata/systems/${systemId}/classifiers/${classifierId}`);
            return response.data;
        },
        enabled: hasClassifier,
    });

    const actor = hasClassifier ? queryResult.data?.data.name : "";

    return [
        actor,
        hasClassifier && queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ];
};
