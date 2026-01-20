import { create } from "zustand";
import { atom, useAtom } from "jotai";

import {
    EditConnectionModalState,
    EditNodeModalState,
    ImportNodeModalState,
    NewConnectionModalState,
    NewNodeModalState
} from "$diagram/types/modals";
import { DiagramUsageItem } from "$diagram/types/diagramUsage";

type ConfirmDeleteClassifierState = {
    active: boolean;
    nodeId: string | null;
    classifierName: string;
    usages: DiagramUsageItem[];
};

type ConfirmDeleteRelationState = {
    active: boolean;
    edgeId: string | null;
    usages: DiagramUsageItem[];
};

const confirmDeleteClassifierAtom = atom<ConfirmDeleteClassifierState>({
    active: false,
    nodeId: null,
    classifierName: "(unknown)",
    usages: [],
});

const confirmDeleteRelationAtom = atom<ConfirmDeleteRelationState>({
    active: false,
    edgeId: null,
    usages: [],
});


export const useConfirmDeleteClassifierModal = () => {
    const [state, setState] = useAtom(confirmDeleteClassifierAtom);

    return {
        ...state,
        open: (payload: {nodeId: string; classifierName: string; usages: DiagramUsageItem[] }) =>
            setState({ active: true, nodeId: payload.nodeId, classifierName: payload.classifierName, usages: payload.usages, }),
        close: () =>
            setState((s) => ({ active: false, nodeId: null, classifierName: "(unknown)", usages: [], })),
    };
};

export const useConfirmDeleteRelationModal = () => {
    const [state, setState] = useAtom(confirmDeleteRelationAtom);

    return {
        ...state,
        open: (payload: {edgeId: string; usages: DiagramUsageItem[] }) =>
            setState({ active: true, edgeId: payload.edgeId, usages: payload.usages, }),
        close: () =>
            setState((s) => ({ active: false, edgeId: null, usages: [], })),
    };
};

export const useNewNodeModal = create<NewNodeModalState>((set) => ({
    active: false,
    open: () => set(() => ({ active: true })),
    close: () => set(() => ({ active: false })),
}));

export const useImportNodeModal = create<ImportNodeModalState>((set) => ({
    active: false,
    open: () => set(() => ({ active: true })),
    close: () => set(() => ({ active: false })),
}));


export const useNewConnectionModal = create<NewConnectionModalState>((set) => ({
    active: false,
    open: (source, target) => set(() => ({ active: true, source, target })),
    close: () =>
        set(() => ({ active: false, source: undefined, target: undefined })),
}));

export const useEditNodeModal = create<EditNodeModalState>((set) => ({
    active: false,
    node: "",
    open: (node) => set(() => ({ active: true, node: node })),
    close: () => set(() => ({ active: false, node: "" })),
}));

export const useEditConnectionModal = create<EditConnectionModalState>(
    (set) => ({
        active: false,
        edge: "",
        open: (edge) => set(() => ({ active: true, edge: edge })),
        close: () => set(() => ({ active: false, edge: "" })),
    }),
);
