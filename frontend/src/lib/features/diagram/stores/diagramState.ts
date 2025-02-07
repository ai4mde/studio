import { applyNodeChanges } from "$diagram/events/node";
import { create } from "zustand";
import { DiagramState } from "../types/diagramState";
// import { applyEdgeChanges, applyNodeChanges } from '../utils/applyChanges'
// import processNodes from '../utils/nodes'
// import processEdges from '../utils/edges'

export const useDiagramStore = create<DiagramState>((set) => ({
    nodes: [],
    edges: [],
    relatedDiagrams: [],
    diagram: "",
    lock: true,
    connecting: false,

    type: "",
    setType: (val) => set(() => ({ type: val })),

    project: "",
    setProject: (val) => set(() => ({ project: val })),

    system: "",
    setSystem: (val) => set(() => ({ system: val })),

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
    nodesFromAPI: (nds) =>
        set(() => ({
            nodes: nds.map((e) => ({
                id: e?.id,
                type: e?.cls?.type,
                position: {
                    x: e.data?.position?.x ?? 0,
                    y: e.data?.position?.y ?? 0,
                },
                parentNode: e?.cls?.parentNode,
                extend: e?.cls?.parentNode ? 'parent' : null,
                connectable: false,
                zIndex: e?.cls?.type === 'swimlane' ? -1 : 1,
                data: e?.cls,
            })),
        })),
    edgesFromAPI: (eds) =>
        set(() => ({
            edges: eds.map((e) => ({
                id: e?.id,
                type: "floating",
                markerEnd: `${e?.rel?.type}-end`,
                markerStart: `${e?.rel?.type}-start`,
                source: e?.source_ptr,
                target: e?.target_ptr,
                data: e?.rel,
            })),
        })),
    relatedDiagramsFromAPI: (rds) =>
        set(() => ({
            relatedDiagrams: rds.map((e) => ({
                id: e?.id,
                name: e?.name,
                type: e?.type,
                nodes: e?.nodes.map((n) => ({
                    id: n?.id,
                    name: n?.name,
                    type: n?.type,
                })),
            })),
        })),
}))
