import { useQuery } from "@tanstack/react-query";
import { authAxios } from "../auth/state/auth";
import { useClassifier } from "../../../api/metadata/hooks/classifier";


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
    const queryResult = useClassifier(systemId, classifierId);

    const actor =
        queryResult.data?.type === "actor"
            ? queryResult.data.data.name
            : undefined;

    return [
        actor,
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ] as const;
};