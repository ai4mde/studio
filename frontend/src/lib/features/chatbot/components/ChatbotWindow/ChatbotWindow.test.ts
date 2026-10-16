import { describe, expect, it } from "vitest";

import { refinementErrorMessage } from "./ChatbotWindow";

describe("refinement error message", () => {
    it("asks for synchronization on a saved-model conflict", () => {
        const conflict = Object.assign(new Error("conflict"), {
            isAxiosError: true,
            response: { status: 409, data: { error: "refinement_conflict" } },
        });

        expect(refinementErrorMessage(conflict)).toContain("Use Sync with AI");
    });

    it("keeps the generic message for other failures", () => {
        expect(refinementErrorMessage(new Error("network error"))).not.toContain("Sync with AI");
    });

    it("explains when process fields cannot survive refinement", () => {
        const conflict = Object.assign(new Error("conflict"), {
            isAxiosError: true,
            response: { status: 409, data: { error: "unsupported_refinement_fields" } },
        });

        expect(refinementErrorMessage(conflict)).toContain("saved process fields");
        expect(refinementErrorMessage(conflict)).not.toContain("Sync with AI");
    });

    it("shows the exact process fields rejected by the backend", () => {
        const conflict = Object.assign(new Error("conflict"), {
            isAxiosError: true,
            response: {
                status: 409,
                data: {
                    error: "unsupported_refinement_fields",
                    detail: "AI refinement cannot safely preserve action.localPrecondition.",
                },
            },
        });

        expect(refinementErrorMessage(conflict)).toContain("action.localPrecondition");
    });
});
