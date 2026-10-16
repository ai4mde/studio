import { HitlCandidateGenerationResponse } from "./types";

const storageKey = (pipelineId: string) => `hitl-candidate-session:${pipelineId}`;
const pipelineKey = (pipelineId: string) => `hitl-pipeline:${pipelineId}`;

export const loadHitlCandidateSession = (
    pipelineId: string,
): HitlCandidateGenerationResponse | null => {
    if (typeof window === "undefined") {
        return null;
    }

    try {
        const raw = window.localStorage.getItem(storageKey(pipelineId));
        if (!raw) {
            return null;
        }
        return JSON.parse(raw) as HitlCandidateGenerationResponse;
    } catch {
        return null;
    }
};

export const saveHitlCandidateSession = (
    pipelineId: string,
    payload: HitlCandidateGenerationResponse,
): void => {
    if (typeof window === "undefined") {
        return;
    }
    window.localStorage.setItem(storageKey(pipelineId), JSON.stringify(payload));
};

export const clearHitlCandidateSession = (pipelineId: string): void => {
    if (typeof window === "undefined") {
        return;
    }
    window.localStorage.removeItem(storageKey(pipelineId));
};

export const markHitlPipeline = (pipelineId: string): void => {
    if (typeof window !== "undefined") {
        window.localStorage.setItem(pipelineKey(pipelineId), "true");
    }
};

export const isHitlPipeline = (pipelineId: string): boolean =>
    typeof window !== "undefined" &&
    (window.localStorage.getItem(pipelineKey(pipelineId)) === "true" ||
        loadHitlCandidateSession(pipelineId) !== null);

export const clearHitlPipeline = (pipelineId: string): void => {
    if (typeof window !== "undefined") {
        window.localStorage.removeItem(pipelineKey(pipelineId));
        window.localStorage.removeItem(storageKey(pipelineId));
    }
};
