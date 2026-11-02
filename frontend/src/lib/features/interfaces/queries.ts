import { authAxios } from "$auth/state/auth";
import { useQuery } from "@tanstack/react-query";
import {
    useClassifiers,
    useClassifier,
} from "../../../api/metadata/hooks/classifier";


export const useSystemClasses = (systemId: string) => {
    const queryResult = useClassifiers(
        { system_id: systemId || undefined },
        !!systemId,
    );

    const classes = (queryResult.data ?? []).filter(
        (classifier) => classifier.type === "class",
    );

    return [
        classes,
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ] as const;
};

export const useClassAttributes = (systemId: string, classId: string) => {
    const queryResult = useQuery({
        queryKey: ["system", "metadata", systemId, "class", classId],
        queryFn: async () => {
            const response = await authAxios.get(
                `/v1/metadata/systems/${systemId}/classifiers/${classId}/`,
            );
            return response.data;
        },
        enabled: !!systemId && !!classId,
    });

    return [
        queryResult.data?.data?.attributes || [],
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ] as const;
};

export const useClassCustomMethods = (systemId: string, classId: string) => {
    const queryResult = useQuery({
        queryKey: ["system", "metadata", systemId, "class", classId, "methods"],
        queryFn: async () => {
            const response = await authAxios.get(
                `/v1/metadata/systems/${systemId}/classifiers/${classId}/`,
            );
            return response.data;
        },
        enabled: !!systemId && !!classId,
    });

    return [
        queryResult.data?.data?.methods || [],
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ] as const;
};

export const useSystemActors = (systemId: string) => {
    const queryResult = useClassifiers(
        { system_id: systemId || undefined },
        !!systemId,
    );

    const actors = (queryResult.data ?? []).filter(
        (classifier) => classifier.type === "actor",
    );

    return [
        actors,
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ] as const;
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
 