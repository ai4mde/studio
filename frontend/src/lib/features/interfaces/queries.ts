import { useQuery } from "@tanstack/react-query";
import { authAxios } from "$auth/state/auth";

export const useSystemClasses = (systemId: string) => {
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

export const useClassAttributes = (systemId: string, classId: string) => {
    const queryResult = useQuery({
        queryKey: ["system", "metadata", systemId, "class", classId],
        queryFn: async () => {
            if (systemId && classId) {
                const response = await authAxios.get(`/v1/metadata/systems/${systemId}/classes/${classId}/`);
                return response.data;
            }
            return [];
        },
    });

    const classAttributes = queryResult.data?.data?.attributes || [];

    return [
        classAttributes,
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ];
};

export const useSystemActors = (systemId: string) => {
    const queryResult = useQuery({
        queryKey: ["system", "metadata", "actors", systemId],
        queryFn: async () => {
            const response = await authAxios.get(`/v1/metadata/systems/${systemId}/actors/`);
            return response.data;
        },
    });

    const actors = queryResult.data?.classifiers || [];

    return [
        actors,
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ];
};