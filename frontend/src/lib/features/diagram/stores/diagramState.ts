import { applyNodeChanges } from "$diagram/events/node";
import { create } from "zustand";
import { DiagramState, RelatedNode } from "../types/diagramState";

export const useDiagramStore = create<DiagramState>((set) => ({
    nodes: [],
    edges: [],
    relatedDiagrams: [],
    uniqueActors: [],
    diagram: "",
    lock: true,
    connecting: false,

    type: "",
    setType: (val) => set(() => ({ type: val })),

    project: "",
    setProject: (val) => set(() => ({ project: val })),

    systemId: "",
    systemName: "",
    system: "",
    setSystem: (id, name = "") => set(() => ({ systemId: id, systemName: name, system: id })),

    refreshLock: () => set(() => ({})),
    requestLock: () => set(() => ({ lock: true })),
    releaseLock: () => set(() => ({ lock: false })),
    setDiagramID: (val) => set(() => ({ diagram: val })),
    setConnecting: (val) => set(() => ({ connecting: val })),
    setNodes: (nodes) => set(() => ({ nodes: nodes })),
    setEdges: (edges) => set(() => ({ edges: edges })),
    setRelatedDiagrams: (relatedDiagrams) => set(() => ({ relatedDiagrams: relatedDiagrams })),
    onNodesChange: (changes) =>
        set((state) => ({
            nodes: applyNodeChanges(changes, state.nodes, state.diagram),
        })),
    onEdgesChange: () =>
        set(() => ({
            // edges: [], // applyEdgeChanges(changes, state.edges, state.diagramURL),
        })),
    nodesFromAPI: (nds) => {
        const swimlaneGroupUUID = nds.filter((n) => n?.cls?.type === 'swimlanegroup')[0]?.id;
        const classifierNodeMap = new Map(
            nds
                .filter((n) => n?.cls_ptr && n?.id)
                .map((n) => [n.cls_ptr, n.id]),
        );
        set(() => ({
            nodes: nds.map((e) => {
                const parentNode = e?.cls?.parentNode
                    ? classifierNodeMap.get(e.cls.parentNode) ?? e.cls.parentNode
                    : (e?.cls?.actorNode ? swimlaneGroupUUID : null);

                return {
                    id: e?.id,
                    type: e?.cls?.type,
                    position: {
                        x: e.data?.position?.x ?? 0,
                        y: e.data?.position?.y ?? 0,
                    },
                    data: {
                        ...e.cls,
                        systemName: e.system_name,
                        systemId: e.system_id,
                    },
                    parentNode,
                    extent: parentNode ? 'parent' : null,
                    connectable: e?.cls?.type === 'swimlanegroup' ? false : true,
                    zIndex: e?.cls?.type === "swimlanegroup" ? -1 : e?.cls?.type === "system_boundary" ? 0 : 1,
                };
            }),
        }))
    },
    edgesFromAPI: (eds) =>
        set(() => ({
            edges: eds.map((e) => ({
                id: e?.id,
                type: "floating",
                markerEnd: `${e?.rel?.type}-end`,
                markerStart: `${e?.rel?.type}-start`,
                source: e?.source_ptr,
                target: e?.target_ptr,
                data: {
                    ...(e?.rel ?? {}),
                    edge_data: (e?.data ?? {}),
                },
            })),
        })),
    relatedDiagramsFromAPI: (rds) => {
        set(() => {
            // Map relatedDiagrams from API response
            const relatedDiagrams = rds.map((e) => ({
                id: e?.id,
                name: e?.name,
                type: e?.type,
                nodes: e?.nodes.map((n) => ({
                    id: n?.id,
                    name: n?.name,
                    type: n?.type,
                    cls: n?.cls,
                    actorNode: n?.actorNode,
                    classAttributes: n?.classAttributes,
                })),
            }));

            // Compute uniqueActors from relatedDiagrams
            const uniqueActors = Array.from(
                relatedDiagrams
                    .filter((diagram) => diagram.type === "usecase")
                    .flatMap((diagram) => diagram.nodes)
                    .filter((node) => node.type === "actor")
                    .reduce((map, node) => {
                        map.set(node.name, node);
                        return map;
                    }, new Map<string, RelatedNode>())
                    .values()
            );

            return { relatedDiagrams, uniqueActors };
        });
    }
}));


