import { useQueries } from "@tanstack/react-query";
import { useMemo } from "react";

import { useDiagram, useDiagrams } from "../../../../api/diagram/hooks/diagram";
import { getDiagram } from "../../../../api/diagram/diagram";
import { queryKeys } from "../../../../api/querykeys";
import type { RelatedDiagram } from "../types/diagramState";
import { classifierTypeFromApi } from "../mutations/fields";

export { useDiagram };

// The old diagram endpoint returned the other diagrams of the system as
// `related_diagrams`. The new API doesn't, so we fetch every diagram of the
// system and map it into the same shape the components expect.
export const useRelatedDiagrams = (systemId: string) => {
    const { data: diagrams = [], dataUpdatedAt: listUpdatedAt } =
        useDiagrams(systemId);

    const results = useQueries({
        queries: diagrams
            .filter((diagram) => !!diagram.id)
            .map((diagram) => ({
                queryKey: queryKeys.diagrams.detail(diagram.id!),
                queryFn: () => getDiagram(diagram.id!),
            })),
    });

    const updatedAt = results.map((r) => r.dataUpdatedAt).join(",");

    const relatedDiagrams = useMemo<RelatedDiagram[]>(
        () =>
            results
                .map((r) => r.data)
                .filter((d): d is NonNullable<typeof d> => !!d)
                .map((diagram) => ({
                    id: diagram.id ?? "",
                    name: diagram.name,
                    type: diagram.type,
                    nodes: diagram.nodes.map((node) => {
                        const data = node.classifier.data as Record<string, any>;

                        return {
                            id: node.id ?? "",
                            name: data?.name ?? "",
                            type: classifierTypeFromApi(node.classifier.type),
                            cls: node.classifier.id ?? "",
                            actorNode: data?.actorNode ?? undefined,
                            classAttributes: data?.attributes ?? [],
                        };
                    }),
                })),
        // eslint-disable-next-line react-hooks/exhaustive-deps
        [updatedAt, listUpdatedAt],
    );

    return {
        relatedDiagrams,
        isSuccess: results.every((r) => r.isSuccess),
    };
};
