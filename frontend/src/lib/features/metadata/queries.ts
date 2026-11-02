import {
    useClassifier,
    useClassifiers,
} from "../../../api/metadata/hooks/classifier";
import { useSystem } from "../../../api/metadata/hooks/system";


// There is no /meta/ endpoint anymore, so we put together the
// system and its classifiers to show roughly the same overview
export const useSystemMetadata = (systemId: string) => {
    const system = useSystem(systemId);
    const classifiers = useClassifiers(
        { system_id: systemId || undefined },
        !!systemId,
    );

    return {
        data: {
            ...system.data,
            classifiers: classifiers.data ?? [],
        },
        isSuccess: system.isSuccess && classifiers.isSuccess,
        isLoading: system.isLoading || classifiers.isLoading,
        error: system.error ?? classifiers.error,
    };
};

export const useActor = (systemId: string, classifierId: string) => {
    const queryResult = useClassifier(systemId, classifierId);

    const actor =
        queryResult.data?.type === "actor"
            ? queryResult.data.data.name
            : undefined;

    return [
        actor,
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ] as const;
};