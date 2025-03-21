import { Edge, EdgeChange, Node, NodeChange } from "reactflow";

export type RelatedNode = {
    id: string;
    name: string;
    type: string;
}

export type RelatedDiagram = {
    id: string;
    name: string;
    type: string;
    nodes: RelatedNode[];
}


export type DiagramState = {
    diagram: string;
    setDiagramID: (id: string) => void;

    type: string;
    setType: (type: string) => void;

    project: string;
    setProject: (project: string) => void;

    system: string;
    setSystem: (system: string) => void;

    lock: boolean;
    refreshLock: () => void;
    requestLock: () => void;
    releaseLock: () => void;

    nodes: Node[];
    setNodes: (nodes: Node[]) => void;
    onNodesChange: (changes: NodeChange[]) => void;
    nodesFromAPI: (nodes: any[]) => void;

    edges: Edge[];
    setEdges: (edges: Edge[]) => void;
    onEdgesChange: (changes: EdgeChange[]) => void;
    edgesFromAPI: (edges: any[]) => void;

    connecting: boolean;
    setConnecting: (val: boolean) => void;

    relatedDiagrams: RelatedDiagram[];
    uniqueActors: RelatedNode[];
    setRelatedDiagrams: (relatedDiagrams: RelatedDiagram[]) => void;
    relatedDiagramsFromAPI: (relatedDiagrams: RelatedDiagram[]) => void;
};
