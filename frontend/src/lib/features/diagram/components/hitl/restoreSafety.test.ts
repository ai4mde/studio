import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("$lib/features/ai/generatorAuth", () => ({ generatorPost: vi.fn() }));
vi.mock("$lib/features/diagram/editorPersistence", () => ({
    waitForEditorPersistence: vi.fn(),
}));

import { generatorPost } from "$lib/features/ai/generatorAuth";
import { waitForEditorPersistence } from "$lib/features/diagram/editorPersistence";
import { restoreAfterEditorSaves } from "./restoreSafety";

describe("restore save barrier", () => {
    beforeEach(() => { vi.clearAllMocks(); });

    it("waits for an older pending save before sending Restore", async () => {
        let finishSave!: () => void;
        vi.mocked(waitForEditorPersistence).mockReturnValue(
            new Promise<void>((resolve) => { finishSave = resolve; }),
        );
        vi.mocked(generatorPost).mockResolvedValue({} as never);

        const restoring = restoreAfterEditorSaves("diagram", "system", "revision");
        expect(generatorPost).not.toHaveBeenCalled();
        finishSave();
        await restoring;

        expect(generatorPost).toHaveBeenCalledWith("/v1/restore-revision", {
            system_id: "system",
            revision_id: "revision",
        });
    });

    it("does not restore after a failed save", async () => {
        vi.mocked(waitForEditorPersistence).mockRejectedValue(new Error("save failed"));

        await expect(restoreAfterEditorSaves("diagram", "system", "revision"))
            .rejects.toThrow("save failed");
        expect(generatorPost).not.toHaveBeenCalled();
    });
});
