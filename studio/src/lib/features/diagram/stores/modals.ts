import {
    EditConnectionModalState,
    EditNodeModalState,
    NewConnectionModalState,
    NewNodeModalState,
} from "$diagram/types/modals";
import { create } from "zustand";

export const useNewNodeModal = create<NewNodeModalState>((set) => ({
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
