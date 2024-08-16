import { useQuery } from "@tanstack/react-query";
import { authAxios } from "$auth/state/auth";

export const useSystemInterfaces = (systemId: string) => {
    const queryResult = useQuery({
        queryKey: ["metdata", "interfaces", systemId],
        queryFn: async () => {
            const response = await authAxios.get(`/v1/metadata/interfaces/`, {
                params: {
                    system: systemId
                }
            });
            return response.data;
        },
    });

    const interfaces = queryResult.data || [];

    return [
        interfaces,
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ];
};

export const useSystemPrototypes = (systemId: string) => {
    const queryResult = useQuery({
        queryKey: ["generator", "prototypes", systemId],
        queryFn: async () => {
            const response = await authAxios.get(`/v1/generator/prototypes/`, {
                params: {
                    system: systemId
                }
            });
            return response.data;
        },
    });

    const prototypes = queryResult.data || [];

    return [
        prototypes,
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ];
};

export const useSystemDiagrams = (systemId: string) => {
    const queryResult = useQuery({
        queryKey: ["diagram", "system", systemId],
        queryFn: async () => {
            const response = await authAxios.get(`/v1/diagram/system/${systemId}/`, {
            });
            return response.data;
        },
    });

    const diagrams = queryResult.data || [];

    return [
        diagrams,
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ];
};

export const getPrototypeStatus = (prototypeName: string) => {
    const queryResult = useQuery({
        queryKey: ["prototype", "status", prototypeName],
        queryFn: async () => {
            const response = await authAxios.get(`/v1/generator/prototypes/status/${prototypeName}/`, {
            });
            return response.data;
        },
    });

    const prototypeStatus = queryResult.data || [];

    return [
        prototypeStatus,
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ];
};