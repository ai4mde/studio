import { authAxios } from "$auth/state/auth";
import { useQuery } from "@tanstack/react-query";

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
                const response = await authAxios.get(`/v1/metadata/systems/${systemId}/classifiers/${classId}/`);
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

export const useClassCustomMethods = (systemId: string, classId: string) => {
    const queryResult = useQuery({
        queryKey: ["system", "metadata", systemId, "class", classId, "methods"],
        queryFn: async () => {
            if (systemId && classId) {
                const response = await authAxios.get(`/v1/metadata/systems/${systemId}/classifiers/${classId}/`);
                return response.data;
            }
            return [];
        },
    });

    const classCustomMethods = queryResult.data?.data?.methods || [];

    return [
        classCustomMethods,
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

export const useSystemActions = (systemId: string, nodeType?: string) => {
    const queryResult = useQuery({
        queryKey: ["system", "metadata", "actionnodes", systemId],
        queryFn: async() => {
            const url = nodeType
                ? `/v1/metadata/systems/${systemId}/nodes/?node_type=${nodeType}`
                : `/v1/metadata/systems/${systemId}/nodes/?node_type=action`;
            const response = await authAxios.get(url);
            return response.data;
        },
    });
 
    const actionNodes = queryResult.data || [];
 
    return [
        actionNodes,
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ]
}
 