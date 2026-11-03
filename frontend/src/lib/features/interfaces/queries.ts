import {
    useClassifiers,
    useClassifier,
} from "../../../api/metadata/hooks/classifier";


export const useSystemClasses = (systemId: string) => {
    const queryResult = useClassifiers(
        { system_id: systemId || undefined },
        !!systemId,
    );

    const classes = (queryResult.data ?? []).filter(
        (classifier) => classifier.type === "class",
    );

    return [
        classes,
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ] as const;
};

// TODO(api): class Attributes and Operations have no API yet, so these stay
// empty until the classifier data includes them
export const useClassAttributes = (systemId: string, classId: string) => {
    const queryResult = useClassifier(systemId, classId);
    const data = queryResult.data?.data as Record<string, any> | undefined;

    return [
        data?.attributes || [],
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ] as const;
};

export const useClassCustomMethods = (systemId: string, classId: string) => {
    const queryResult = useClassifier(systemId, classId);
    const data = queryResult.data?.data as Record<string, any> | undefined;

    return [
        data?.methods || [],
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ] as const;
};

export const useSystemActors = (systemId: string) => {
    const queryResult = useClassifiers(
        { system_id: systemId || undefined },
        !!systemId,
    );

    const actors = (queryResult.data ?? []).filter(
        (classifier) => classifier.type === "actor",
    );

    return [
        actors,
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ] as const;
};

// The /nodes/ endpoint is gone, so use the classifiers of the system instead.
// Keep the old { id, cls } shape that the interface components expect.
export const useSystemActions = (systemId: string, nodeType?: string) => {
    const queryResult = useClassifiers(
        { system_id: systemId || undefined },
        !!systemId,
    );

    const type = nodeType ?? "action";
    const actionNodes = (queryResult.data ?? [])
        .filter((classifier) => classifier.type === type)
        .map((classifier) => ({
            id: classifier.id,
            cls: classifier.data as Record<string, any>,
        }));

    return [
        actionNodes,
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ] as const;
}
