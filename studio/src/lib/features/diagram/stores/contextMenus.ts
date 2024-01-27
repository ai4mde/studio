import { Edge, Node } from "reactflow";
import { create } from "zustand";
import {
    EdgeContextMenuState,
    NodeContextMenuState,
    PaneContextMenuState,
    SelectionContextMenuState,
} from "../types/contextMenus";

export const usePaneContextMenu = create<PaneContextMenuState>((set) => ({
    active: false,
    x: 0,
    y: 0,
    open: (x: number, y: number) => set(() => ({ active: true, x: x, y: y })),
    close: () => set(() => ({ active: false })),
}));

export const useNodeContextMenu = create<NodeContextMenuState>((set) => ({
    active: false,
    x: 0,
    y: 0,
    node: undefined,
    open: (x: number, y: number, node: Node) =>
        set(() => ({ active: true, x: x, y: y, node: node })),
    close: () => set(() => ({ active: false, node: undefined })),
}));

export const useSelectionContextMenu = create<SelectionContextMenuState>(
    (set) => ({
        active: false,
        x: 0,
        y: 0,
        nodes: undefined,
        edges: undefined,
        open: (x: number, y: number, nodes: Node[], edges: Edge[]) =>
            set(() => ({
                active: true,
                x: x,
                y: y,
                nodes: nodes,
                edges: edges,
            })),
        close: () =>
            set(() => ({ active: false, nodes: undefined, edges: undefined })),
    })
);

export const useEdgeContextMenu = create<EdgeContextMenuState>((set) => ({
    active: false,
    x: 0,
    y: 0,
    edge: undefined,
    open: (x: number, y: number, edge: Edge) =>
        set(() => ({ active: true, x: x, y: y, edge: edge })),
    close: () => set(() => ({ active: false, edge: undefined })),
}));
