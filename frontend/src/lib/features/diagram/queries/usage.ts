import { queryClient } from "$shared/hooks/queryClient";
import { queryKeys } from "../../../../api/querykeys";
import { getDiagram, listDiagrams } from "../../../../api/diagram/diagram";
import type { DiagramReadFull } from "../../../../api/diagram/diagram";
import { deleteNode } from "../../../../api/diagram/node";
import { deleteEdge } from "../../../../api/diagram/edge";
import type { DiagramUsageItem } from "../types/diagramUsage";

// The old backend had classifier-usage / relation-usage and hard delete
// endpoints. The new one doesn't, but classifiers and relations belong to a
// single system, so we can find every usage by looking through the diagrams
// of that system.

const fetchSystemDiagrams = async (
    systemId: string,
): Promise<DiagramReadFull[]> => {
    const diagrams = await queryClient.fetchQuery({
        queryKey: queryKeys.diagrams.list(systemId),
        queryFn: () => listDiagrams(systemId),
    });

    return Promise.all(
        diagrams
            .filter((diagram) => !!diagram.id)
            .map((diagram) =>
                queryClient.fetchQuery({
                    queryKey: queryKeys.diagrams.detail(diagram.id!),
                    queryFn: () => getDiagram(diagram.id!),
                }),
            ),
    );
};

type Usage = {
    diagramId: string;
    elementId: string;
};

const toUsageItems = (
    usages: Usage[],
    diagrams: DiagramReadFull[],
    systemId: string,
    systemName: string,
): DiagramUsageItem[] => {
    const seen = new Set<string>();

    return usages
        .filter(({ diagramId }) => {
            if (seen.has(diagramId)) return false;
            seen.add(diagramId);
            return true;
        })
        .map(({ diagramId }) => ({
            diagram_id: diagramId,
            diagram_name:
                diagrams.find((d) => d.id === diagramId)?.name ?? "",
            system_id: systemId,
            system_name: systemName,
        }));
};

const findClassifierNodes = (
    diagrams: DiagramReadFull[],
    classifierId: string,
): Usage[] =>
    diagrams.flatMap((diagram) =>
        diagram.nodes
            .filter((node) => node.classifier.id === classifierId && node.id)
            .map((node) => ({ diagramId: diagram.id!, elementId: node.id! })),
    );

const findRelationEdges = (
    diagrams: DiagramReadFull[],
    relationId: string,
): Usage[] =>
    diagrams.flatMap((diagram) =>
        diagram.edges
            .filter((edge) => edge.relation.id === relationId && edge.id)
            .map((edge) => ({ diagramId: diagram.id!, elementId: edge.id! })),
    );

// Usages of a classifier in diagrams other than the current one
export const getClassifierUsage = async (
    systemId: string,
    systemName: string,
    currentDiagramId: string,
    classifierId: string,
) => {
    const diagrams = await fetchSystemDiagrams(systemId);
    const usages = findClassifierNodes(diagrams, classifierId).filter(
        (usage) => usage.diagramId !== currentDiagramId,
    );

    return toUsageItems(usages, diagrams, systemId, systemName);
};

// Usages of a relation in diagrams other than the current one
export const getRelationUsage = async (
    systemId: string,
    systemName: string,
    currentDiagramId: string,
    relationId: string,
) => {
    const diagrams = await fetchSystemDiagrams(systemId);
    const usages = findRelationEdges(diagrams, relationId).filter(
        (usage) => usage.diagramId !== currentDiagramId,
    );

    return toUsageItems(usages, diagrams, systemId, systemName);
};

// Deleting the last node of a classifier deletes the classifier on the
// backend, so removing every node is the same as the old hard delete
export const deleteClassifierEverywhere = async (
    systemId: string,
    classifierId: string,
) => {
    const diagrams = await fetchSystemDiagrams(systemId);
    const nodes = findClassifierNodes(diagrams, classifierId);

    for (const { elementId } of nodes) {
        await deleteNode(elementId);
    }

    await queryClient.invalidateQueries();
};

// Same idea for relations and their edges
export const deleteRelationEverywhere = async (
    systemId: string,
    relationId: string,
) => {
    const diagrams = await fetchSystemDiagrams(systemId);
    const edges = findRelationEdges(diagrams, relationId);

    for (const { elementId } of edges) {
        await deleteEdge(elementId);
    }

    await queryClient.invalidateQueries();
};
