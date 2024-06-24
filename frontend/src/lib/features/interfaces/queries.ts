import { useQuery } from "@tanstack/react-query";
import { authAxios } from "$auth/state/auth";

export const useSystemClasses = (systemId) => {
    const queryResult = useQuery({
        queryKey: ["system", "metadata", systemId],
        queryFn: async () => {
            const response = await authAxios.get(`/v1/metadata/systems/${systemId}/classes/`);
            return response.data;
        },
    });

    const classes = queryResult.data?.classifiers || [];

    return [
        classes,
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ];
};
