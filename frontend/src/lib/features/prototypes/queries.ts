import { useQueries, useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { authAxios } from "$auth/state/auth";
import { useInterfaces } from "../../../api/metadata/hooks/interface";
import { useDiagrams } from "../../../api/diagram/hooks/diagram";
import { getDiagram } from "../../../api/diagram/diagram";
import { queryKeys } from "../../../api/querykeys";

export const useSystemInterfaces = (systemId: string) => {
    const queryResult = useInterfaces({ system_id: systemId });

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

// The prototype metadata needs the full diagrams (with nodes and edges),
// the list endpoint only returns summaries so fetch every diagram as well
export const useSystemDiagrams = (systemId: string) => {
    const list = useDiagrams(systemId);

    const details = useQueries({
        queries: (list.data ?? [])
            .filter((diagram) => !!diagram.id)
            .map((diagram) => ({
                queryKey: queryKeys.diagrams.detail(diagram.id!),
                queryFn: () => getDiagram(diagram.id!),
            })),
    });

    const updatedAt = details.map((detail) => detail.dataUpdatedAt).join(",");
    const diagrams = useMemo(
        () =>
            details
                .map((detail) => detail.data)
                .filter((diagram) => !!diagram),
        // eslint-disable-next-line react-hooks/exhaustive-deps
        [updatedAt],
    );

    return [
        diagrams,
        list.isSuccess && details.every((detail) => detail.isSuccess),
        list.isLoading || details.some((detail) => detail.isLoading),
        list.error ?? details.find((detail) => detail.error)?.error ?? null,
    ];
};
