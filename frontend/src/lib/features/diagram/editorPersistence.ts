import { authAxios } from "$auth/state/auth";
import { create } from "zustand";

type EditorPersistenceState = {
    pendingByDiagram: Record<string, number>;
    failures: Record<string, { diagramId: string; message: string }>;
};

export const useEditorPersistence = create<EditorPersistenceState>(() => ({
    pendingByDiagram: {},
    failures: {},
}));

type TrackedRequest = {
    diagramId: string;
    key: string;
};

const requestKeys = new WeakMap<object, TrackedRequest>();
const idleWaiters = new Map<string, Set<() => void>>();
let installed = false;

const editorWriteDiagram = (method?: string, url?: string) => {
    if (
        !method ||
        !url ||
        !["delete", "patch", "post", "put"].includes(method.toLowerCase())
    ) {
        return null;
    }
    return url.match(/\/v1\/diagram\/([^/]+)/)?.[1] ?? null;
};

const finishRequest = ({ diagramId, key }: TrackedRequest, error?: unknown) => {
    useEditorPersistence.setState((state) => {
        const failures = { ...state.failures };
        const pendingByDiagram = { ...state.pendingByDiagram };
        if (error) {
            failures[key] = {
                diagramId,
                message: "The editor could not save a recent change.",
            };
        } else {
            delete failures[key];
        }
        pendingByDiagram[diagramId] = Math.max(
            0,
            (pendingByDiagram[diagramId] ?? 0) - 1,
        );
        return {
            pendingByDiagram,
            failures,
        };
    });

    if ((useEditorPersistence.getState().pendingByDiagram[diagramId] ?? 0) === 0) {
        idleWaiters.get(diagramId)?.forEach((resolve) => resolve());
        idleWaiters.delete(diagramId);
    }
};

export const installEditorPersistenceTracking = () => {
    if (installed) {
        return;
    }
    installed = true;

    authAxios.interceptors.request.use(
        (config) => {
            const diagramId = editorWriteDiagram(config.method, config.url);
            if (diagramId) {
                const key = `${config.method?.toLowerCase()}:${config.url}`;
                requestKeys.set(config, { diagramId, key });
                useEditorPersistence.setState((state) => ({
                    pendingByDiagram: {
                        ...state.pendingByDiagram,
                        [diagramId]: (state.pendingByDiagram[diagramId] ?? 0) + 1,
                    },
                }));
            }
            return config;
        },
        undefined,
        { synchronous: true },
    );

    authAxios.interceptors.response.use(
        (response) => {
            const key = requestKeys.get(response.config);
            if (key) {
                finishRequest(key);
            }
            return response;
        },
        (error) => {
            const key = error?.config ? requestKeys.get(error.config) : undefined;
            if (key) {
                finishRequest(key, error);
            }
            return Promise.reject(error);
        },
    );
};

export const waitForEditorPersistence = async (diagramId: string) => {
    if ((useEditorPersistence.getState().pendingByDiagram[diagramId] ?? 0) > 0) {
        await new Promise<void>((resolve) => {
            const waiters = idleWaiters.get(diagramId) ?? new Set();
            waiters.add(resolve);
            idleWaiters.set(diagramId, waiters);
        });
    }
    if (
        Object.values(useEditorPersistence.getState().failures).some(
            (failure) => failure.diagramId === diagramId,
        )
    ) {
        throw new Error("Recent editor changes have not been saved successfully.");
    }
};
