import { authAxios } from "$auth/state/auth";
import { create } from "zustand";

type EditorPersistenceState = {
    pendingCount: number;
    failures: Record<string, string>;
};

export const useEditorPersistence = create<EditorPersistenceState>(() => ({
    pendingCount: 0,
    failures: {},
}));

const requestKeys = new WeakMap<object, string>();
const idleWaiters = new Set<() => void>();
let installed = false;

const isEditorWrite = (method?: string, url?: string) =>
    Boolean(
        method &&
            url &&
            ["delete", "patch", "post", "put"].includes(method.toLowerCase()) &&
            /\/v1\/diagram\//.test(url),
    );

const finishRequest = (key: string, error?: unknown) => {
    useEditorPersistence.setState((state) => {
        const failures = { ...state.failures };
        if (error) {
            failures[key] = "The editor could not save a recent change.";
        } else {
            delete failures[key];
        }
        return {
            pendingCount: Math.max(0, state.pendingCount - 1),
            failures,
        };
    });

    if (useEditorPersistence.getState().pendingCount === 0) {
        idleWaiters.forEach((resolve) => resolve());
        idleWaiters.clear();
    }
};

export const installEditorPersistenceTracking = () => {
    if (installed) {
        return;
    }
    installed = true;

    authAxios.interceptors.request.use(
        (config) => {
            if (isEditorWrite(config.method, config.url)) {
                const key = `${config.method?.toLowerCase()}:${config.url}`;
                requestKeys.set(config, key);
                useEditorPersistence.setState((state) => ({
                    pendingCount: state.pendingCount + 1,
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

export const waitForEditorPersistence = async () => {
    if (useEditorPersistence.getState().pendingCount > 0) {
        await new Promise<void>((resolve) => idleWaiters.add(resolve));
    }
    if (Object.keys(useEditorPersistence.getState().failures).length > 0) {
        throw new Error("Recent editor changes have not been saved successfully.");
    }
};
