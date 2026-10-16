import { beforeEach, describe, expect, it, vi } from "vitest";

import { authAxios, useAuthStore } from "$auth/state/auth";
import { generatorPost } from "./generatorAuth";

vi.mock("$auth/state/auth", () => ({
    authAxios: { post: vi.fn() },
    useAuthStore: { getState: vi.fn() },
}));

describe("Generator bearer requests", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("reads the persisted token when making a write request", async () => {
        vi.mocked(useAuthStore.getState).mockReturnValue({
            bearerToken: "stored-token",
            isAuthenticated: true,
            expires: Date.now() + 60_000,
        } as never);

        await generatorPost("/v1/generate-model", { process_text: "review" });

        expect(authAxios.post).toHaveBeenCalledWith(
            "/v1/generate-model",
            { process_text: "review" },
            { headers: { Authorization: "Bearer stored-token" } },
        );
    });

    it("does not use a leftover token after logout", async () => {
        vi.mocked(useAuthStore.getState).mockReturnValue({
            bearerToken: "leftover-token",
            isAuthenticated: false,
            expires: Date.now() + 60_000,
        } as never);

        await expect(generatorPost("/v1/refine-model", { instruction: "review" }))
            .rejects.toThrow("Sign in again");

        expect(authAxios.post).not.toHaveBeenCalled();
    });

    it("does not send an expired token", async () => {
        vi.mocked(useAuthStore.getState).mockReturnValue({
            bearerToken: "expired-token",
            isAuthenticated: true,
            expires: Date.now() - 60_000,
        } as never);

        await expect(generatorPost("/v1/refine-model", { instruction: "review" }))
            .rejects.toThrow("Sign in again");

        expect(authAxios.post).not.toHaveBeenCalled();
    });
});
