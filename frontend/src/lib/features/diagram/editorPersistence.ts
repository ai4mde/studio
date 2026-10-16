import { authAxios } from "$auth/state/auth";
import { create } from "zustand";

type EditorPersistenceState = {
    pendingByDiagram: Record<string, number>;
    failures: Record<string, { diagramId: string; message: string; sequence: number }>;
};

export const useEditorPersistence = create<EditorPersistenceState>(() => ({
    pendingByDiagram: {},
    failures: {},
}));

type TrackedRequest = {
    diagramId: string;
    keys: string[];
    sequence: number;
};

const requestKeys = new WeakMap<object, TrackedRequest>();
const idleWaiters = new Map<string, Set<() => void>>();
const latestSuccessfulByKey = new Map<string, number>();
let nextSequence = 0;
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

const stableValue = (value: unknown): string =>
    JSON.stringify(value, (_key, nested) =>
        nested && typeof nested === "object" && !Array.isArray(nested)
            ? Object.fromEntries(Object.entries(nested).sort(([a], [b]) => a.localeCompare(b)))
            : nested,
    ) ?? "undefined";

const editedFields = (method: string, data: unknown, sequence: number): string[] => {
    // Only PATCH has the editor API's documented shallow-merge semantics.
    // Other writes cannot be identified as safe retries from their payloads.
    if (method !== "patch") {
        return [`operation:${sequence}`];
    }
    let payload = data;
    if (typeof payload === "string") {
        try {
            payload = JSON.parse(payload);
        } catch {
            return [`operation:${sequence}`];
        }
    }
    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
        return [`operation:${sequence}`];
    }
    // The editor API shallow-merges cls, rel and data. Their immediate child
    // fields are the smallest units that a later PATCH can actually replace.
    const fields = Object.entries(payload).flatMap(([scope, value]) =>
        value && typeof value === "object" && !Array.isArray(value)
            ? Object.entries(value).map(
                ([field, editedValue]) => `${scope}.${field}:${stableValue(editedValue)}`,
            )
            : [`${scope}:${stableValue(value)}`],
    );
    return fields.length ? fields : [`operation:${sequence}`];
};

const finishRequest = ({ diagramId, keys, sequence }: TrackedRequest, error?: unknown) => {
    useEditorPersistence.setState((state) => {
        const failures = { ...state.failures };
        const pendingByDiagram = { ...state.pendingByDiagram };
        for (const key of keys) {
            if (error) {
                if (
                    sequence > (latestSuccessfulByKey.get(key) ?? 0) &&
                    sequence > (failures[key]?.sequence ?? 0)
                ) {
                    failures[key] = {
                        diagramId,
                        message: "The editor could not save a recent change.",
                        sequence,
                    };
                }
            } else {
                latestSuccessfulByKey.set(key, Math.max(sequence, latestSuccessfulByKey.get(key) ?? 0));
                if (failures[key] && sequence > failures[key].sequence) {
                    delete failures[key];
                }
            }
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
                const sequence = ++nextSequence;
                const method = config.method?.toLowerCase() ?? "";
                const keys = editedFields(method, config.data, sequence).map(
                    (field) => `${method}:${config.url}:${field}`,
                );
                requestKeys.set(config, { diagramId, keys, sequence });
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
