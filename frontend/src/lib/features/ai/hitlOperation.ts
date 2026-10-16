import { create } from "zustand";

export type HitlOperation = "refinement" | "restore" | "sync";

type HitlOperationState = {
    activeOperation: HitlOperation | null;
};

export const useHitlOperation = create<HitlOperationState>(() => ({
    activeOperation: null,
}));

export const runHitlOperation = async <T>(
    operation: HitlOperation,
    action: () => Promise<T>,
): Promise<T> => {
    if (useHitlOperation.getState().activeOperation !== null) {
        throw new Error("Another revision operation is already running.");
    }

    useHitlOperation.setState({ activeOperation: operation });
    try {
        return await action();
    } finally {
        if (useHitlOperation.getState().activeOperation === operation) {
            useHitlOperation.setState({ activeOperation: null });
        }
    }
};
