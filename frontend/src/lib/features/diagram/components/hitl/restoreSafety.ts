import { generatorPost } from "$lib/features/ai/generatorAuth";
import { waitForEditorPersistence } from "$lib/features/diagram/editorPersistence";

export const restoreAfterEditorSaves = async (
    diagramId: string,
    systemId: string | undefined,
    revisionId: string,
) => {
    await waitForEditorPersistence(diagramId);
    await generatorPost("/v1/restore-revision", {
        system_id: systemId,
        revision_id: revisionId,
    });
};
