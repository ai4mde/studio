import { authAxios } from "$lib/features/auth/state/auth";

const SESSION_KEY = "studio_session_id";

export function getSessionId(): string {
    let id = sessionStorage.getItem(SESSION_KEY);
    if (!id) {
        id = globalThis.crypto.randomUUID();
        sessionStorage.setItem(SESSION_KEY, id);
    }
    return id;
}

export function trackEvent(event_type: string, metadata: Record<string, unknown> = {}) {
    authAxios
        .post("/v1/analytics/event", {
            session_id: getSessionId(),
            event_type,
            metadata,
        })
        .catch(() => {});
}
