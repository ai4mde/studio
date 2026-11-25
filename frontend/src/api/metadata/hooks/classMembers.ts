import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { queryKeys } from "../../querykeys";
import {
    listAttributes,
    createAttribute,
    updateAttribute,
    deleteAttribute,
    listOperations,
    createOperation,
    updateOperation,
    deleteOperation,
} from "../classMembers";

export const useAttributes = (classifierId: string | null | undefined) => {
    return useQuery({
        queryKey: queryKeys.classifiers.attributes(classifierId ?? ""),
        queryFn: () => listAttributes(classifierId!),
        enabled: Boolean(classifierId),
    });
};

export const useOperations = (classifierId: string | null | undefined) => {
    return useQuery({
        queryKey: queryKeys.classifiers.operations(classifierId ?? ""),
        queryFn: () => listOperations(classifierId!),
        enabled: Boolean(classifierId),
    });
};

// Compare the edited list with what the server has and send
// a delete, update or create for each item that differs
const syncItems = async <T extends { id?: string | null }>(
    original: T[],
    edited: T[],
    toPayload: (item: T) => Record<string, unknown>,
    api: {
        create: (payload: any) => Promise<unknown>;
        update: (id: string, payload: any) => Promise<unknown>;
        remove: (id: string) => Promise<unknown>;
    },
) => {
    const editedIds = new Set(edited.map((item) => item.id).filter(Boolean));

    for (const item of original) {
        if (item.id && !editedIds.has(item.id)) {
            await api.remove(item.id);
        }
    }

    for (const item of edited) {
        const payload = toPayload(item);

        if (!item.id) {
            await api.create(payload);
            continue;
        }

        const before = original.find((o) => o.id === item.id);
        if (before && JSON.stringify(toPayload(before)) !== JSON.stringify(payload)) {
            await api.update(item.id, payload);
        }
    }
};

export const useSaveAttributes = (classifierId: string) => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ original, edited }: { original: any[]; edited: any[] }) =>
            syncItems(
                original,
                edited,
                (a) => ({
                    name: a.name ?? "",
                    type: a.type,
                    derived: !!a.derived,
                    enum_id: a.type === "enum" ? a.enum ?? null : null,
                    description: a.description ?? null,
                    body: a.body ?? null,
                }),
                {
                    create: (payload) => createAttribute(classifierId, payload),
                    update: updateAttribute,
                    remove: deleteAttribute,
                },
            ),

        onSettled: () =>
            queryClient.invalidateQueries({
                queryKey: queryKeys.classifiers.attributes(classifierId),
            }),
    });
};

export const useSaveOperations = (classifierId: string) => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({ original, edited }: { original: any[]; edited: any[] }) =>
            syncItems(
                original,
                edited,
                (o) => ({
                    name: o.name ?? "",
                    type: o.type,
                    description: o.description ?? null,
                    body: o.body ?? null,
                }),
                {
                    create: (payload) => createOperation(classifierId, payload),
                    update: updateOperation,
                    remove: deleteOperation,
                },
            ),

        onSettled: () =>
            queryClient.invalidateQueries({
                queryKey: queryKeys.classifiers.operations(classifierId),
            }),
    });
};