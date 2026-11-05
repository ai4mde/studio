import { useClassifiers, useClassifier } from "../../../api/metadata/hooks/classifier";
import { useAttributes, useOperations } from "../../../api/metadata/hooks/classMembers";


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

export const useClassAttributes = (systemId: string, classId: string) => {
    const queryResult = useAttributes(classId);

    return [
        queryResult.data ?? [],
        queryResult.isSuccess,
        queryResult.isLoading,
        queryResult.error,
    ] as const;
};

export const useClassCustomMethods = (systemId: string, classId: string) => {
    const queryResult = useOperations(classId);

    return [
        queryResult.data ?? [],
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
