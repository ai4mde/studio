import { authAxios } from "$lib/features/auth/state/auth";
import { useQuery } from "@tanstack/react-query";

export const useSystemClassClassifiers = (systemId: string) => {
    const queryResult = useQuery({
        queryKey: ["system", "metadata", systemId],
        queryFn: async () => {
            const response = await authAxios.get(`/v1/metadata/systems/${systemId}/classifiers/`);
            return response.data;
        },
    });

    const classifiers = queryResult.data?.classifiers?.filter(
        (classifier) => classifier.data?.type === "enum" || classifier.data?.type === "class"
    ) || [];

    return [
        classifiers,
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ];
};

export const useSystemActivityClassifiers = (systemId: string) => {
    const queryResult = useQuery({
        queryKey: ["system", "metadata", systemId],
        queryFn: async () => {
            const response = await authAxios.get(`/v1/metadata/systems/${systemId}/classifiers/`);
            return response.data;
        },
    });

    const classifiers = queryResult.data?.classifiers?.filter(
        (classifier) => classifier.data?.type === "action"
    ) || [];

    return [
        classifiers,
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ];
};

export const useSystemUsecaseClassifiers = (systemId: string) => {
    const queryResult = useQuery({
        queryKey: ["system", "metadata", systemId],
        queryFn: async () => {
            const response = await authAxios.get(`/v1/metadata/systems/${systemId}/classifiers/`);
            return response.data;
        },
    });

    const classifiers = queryResult.data?.classifiers?.filter(
        (classifier) => classifier.data?.type === "actor" || classifier.data?.type === "usecase"
    ) || [];

    return [
        classifiers,
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ];
};