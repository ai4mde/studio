import { AxiosError, type AxiosResponse } from "axios";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("$auth/state/auth", async () => ({
    authAxios: (await import("axios")).default.create(),
}));

import { authAxios } from "$auth/state/auth";
import {
    installEditorPersistenceTracking,
    useEditorPersistence,
    waitForEditorPersistence,
} from "./editorPersistence";

type DeferredRequest = {
    succeed: () => void;
    fail: () => void;
};

const requests: DeferredRequest[] = [];
let testIndex = 0;

beforeAll(() => installEditorPersistenceTracking());
beforeEach(() => {
    requests.length = 0;
    useEditorPersistence.setState({ pendingByDiagram: {}, failures: {} });
    authAxios.defaults.adapter = (config) =>
        new Promise<AxiosResponse>((resolve, reject) => {
            requests.push({
                succeed: () => resolve({ data: {}, status: 200, statusText: "OK", headers: {}, config }),
                fail: () => reject(new AxiosError("save failed", "ERR_BAD_RESPONSE", config)),
            });
        });
});

const overlappingPatches = async () => {
    const diagramId = `persistence-${++testIndex}`;
    const url = `/v1/diagram/${diagramId}/node/action`;
    const older = authAxios.patch(url, { body: "intended edit" });
    const newer = authAxios.patch(url, { body: "intended edit" });
    const settled = Promise.allSettled([older, newer]);
    await vi.waitFor(() => expect(requests).toHaveLength(2));
    return { diagramId, settled };
};

describe("overlapping editor PATCH tracking", () => {
    it("does not let an older success clear a newer failure", async () => {
        const { diagramId, settled } = await overlappingPatches();
        requests[1].fail();
        requests[0].succeed();
        await settled;

        expect(useEditorPersistence.getState().pendingByDiagram[diagramId]).toBe(0);
        await expect(waitForEditorPersistence(diagramId)).rejects.toThrow("not been saved");
    });

    it("clears an older failure when a newer retry succeeds", async () => {
        const { diagramId, settled } = await overlappingPatches();
        requests[0].fail();
        requests[1].succeed();
        await settled;

        await expect(waitForEditorPersistence(diagramId)).resolves.toBeUndefined();
    });

    it("ignores a stale failure after a newer save succeeds", async () => {
        const { diagramId, settled } = await overlappingPatches();
        requests[1].succeed();
        requests[0].fail();
        await settled;

        await expect(waitForEditorPersistence(diagramId)).resolves.toBeUndefined();
    });

    it("does not treat a different value for the same field as a retry", async () => {
        const diagramId = `persistence-${++testIndex}`;
        const url = `/v1/diagram/${diagramId}/node/action`;
        const intended = authAxios.patch(url, { cls: { name: "Human edit" } });
        const different = authAxios.patch(url, { cls: { name: "Stale value" } });
        const settled = Promise.allSettled([intended, different]);
        await vi.waitFor(() => expect(requests).toHaveLength(2));
        requests[0].fail();
        requests[1].succeed();
        await settled;
        await expect(waitForEditorPersistence(diagramId)).rejects.toThrow("not been saved");
    });

    it.each(["failure first", "success first"])(
        "keeps a failed name edit when a position edit succeeds (%s)",
        async (order) => {
            const diagramId = `persistence-${++testIndex}`;
            const url = `/v1/diagram/${diagramId}/node/action`;
            const name = authAxios.patch(url, { cls: { name: "Human edit" } });
            const position = authAxios.patch(url, { data: { position: { x: 10, y: 20 } } });
            const settled = Promise.allSettled([name, position]);
            await vi.waitFor(() => expect(requests).toHaveLength(2));
            if (order === "failure first") {
                requests[0].fail();
                requests[1].succeed();
            } else {
                requests[1].succeed();
                requests[0].fail();
            }
            await settled;

            await expect(waitForEditorPersistence(diagramId)).rejects.toThrow("not been saved");
        },
    );

    it("only clears the fields actually retried on the same model", async () => {
        const diagramId = `persistence-${++testIndex}`;
        const url = `/v1/diagram/${diagramId}/node/action`;
        const failed = authAxios.patch(url, { cls: { name: "Edited", body: "Important" } });
        await vi.waitFor(() => expect(requests).toHaveLength(1));
        requests[0].fail();
        await Promise.allSettled([failed]);

        const nameRetry = authAxios.patch(url, { cls: { name: "Edited" } });
        await vi.waitFor(() => expect(requests).toHaveLength(2));
        requests[1].succeed();
        await nameRetry;
        await expect(waitForEditorPersistence(diagramId)).rejects.toThrow("not been saved");

        const bodyRetry = authAxios.patch(url, { cls: { body: "Important" } });
        await vi.waitFor(() => expect(requests).toHaveLength(3));
        requests[2].succeed();
        await bodyRetry;
        await expect(waitForEditorPersistence(diagramId)).resolves.toBeUndefined();
    });

    it("keeps failures for separate models in the same diagram", async () => {
        const diagramId = `persistence-${++testIndex}`;
        const first = authAxios.patch(`/v1/diagram/${diagramId}/node/first`, { cls: { name: "A" } });
        const second = authAxios.patch(`/v1/diagram/${diagramId}/node/second`, { cls: { name: "B" } });
        const settled = Promise.allSettled([first, second]);
        await vi.waitFor(() => expect(requests).toHaveLength(2));
        requests[0].fail();
        requests[1].succeed();
        await settled;
        await expect(waitForEditorPersistence(diagramId)).rejects.toThrow("not been saved");
    });

    it("waits for every pending edit and blocks Sync after an unresolved failure", async () => {
        const diagramId = `persistence-${++testIndex}`;
        const url = `/v1/diagram/${diagramId}/node/action`;
        const name = authAxios.patch(url, { cls: { name: "Edited" } });
        const weight = authAxios.patch(url, { rel: { weight: "2" } });
        const settled = Promise.allSettled([name, weight]);
        await vi.waitFor(() => expect(requests).toHaveLength(2));
        const syncGate = waitForEditorPersistence(diagramId);
        let completed = false;
        void syncGate.finally(() => { completed = true; }).catch(() => {});

        requests[0].succeed();
        await vi.waitFor(() => expect(useEditorPersistence.getState().pendingByDiagram[diagramId]).toBe(1));
        expect(completed).toBe(false);
        requests[1].fail();
        await settled;
        await expect(syncGate).rejects.toThrow("not been saved");
    });
});
