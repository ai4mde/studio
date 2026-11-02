import { authAxios } from "$lib/features/auth/state/auth";
import { queryClient } from "$lib/shared/hooks/queryClient";
import { queryKeys } from "../../../../api/querykeys";
import {
    createNode,
    updateNode,
    deleteNode as deleteApiNode,
} from "../../../../api/diagram/node";
import type { NodeCreate, NodeUpdate } from "../../../../api/diagram/node";
import {
    createEdge,
    updateEdge,
    deleteEdge as deleteApiEdge,
} from "../../../../api/diagram/edge";
import type { EdgeCreate, EdgeUpdate } from "../../../../api/diagram/edge";
import { classifierDataToApi, classifierTypeToApi } from "./fields";

// Fields that now live on the node itself instead of in the classifier data
const NODE_FIELDS = ["height", "width", "color", "font"] as const;

const invalidateDiagram = (diagram: string) =>
    queryClient.invalidateQueries({
        queryKey: queryKeys.diagrams.detail(diagram),
    });

const invalidateClassifiers = () =>
    queryClient.invalidateQueries({
        queryKey: queryKeys.classifiers.all,
    });

export const addNode = async (diagram: string, data: any) => {
    // TODO Temporary fix, input should not be flat. The data fields should be nested
    const { type, position, ...classifierData } = data;

    const nodeFields: Record<string, unknown> = {};
    for (const field of NODE_FIELDS) {
        if (field in classifierData) {
            nodeFields[field] = classifierData[field];
            delete classifierData[field];
        }
    }

    await createNode(diagram, {
        classifier: {
            type: classifierTypeToApi(type),
            data: classifierDataToApi(classifierData),
        },
        x_position: position?.x ?? 0,
        y_position: position?.y ?? 0,
        ...nodeFields,
    } as NodeCreate);

    invalidateDiagram(diagram);
    invalidateClassifiers();
};

export const importNode = async (diagram: string, id: string) => {
    // TODO(api): the new backend has no way to add a node for an existing classifier
    await authAxios.post(`/v1/diagram/${diagram}/node/import/${id}/`, {
    });

    invalidateDiagram(diagram);
};

// Old payloads looked like { cls: {...classifier data}, data: { position } }.
// Translate them to the new NodeUpdate shape.
export const toNodeUpdate = (data: any): NodeUpdate => {
    const payload: Record<string, unknown> = {};

    const position = data?.data?.position ?? data?.position;
    if (position) {
        payload.x_position = position.x;
        payload.y_position = position.y;
    }

    if ("parent_id" in (data ?? {})) {
        payload.parent_id = data.parent_id;
    }

    if (data?.cls) {
        const classifierData = { ...data.cls };

        for (const field of NODE_FIELDS) {
            if (field in classifierData) {
                payload[field] = classifierData[field];
                delete classifierData[field];
            }
        }

        // These are only added on the frontend when reading nodes
        delete classifierData.classifierId;
        delete classifierData.systemId;
        delete classifierData.type;

        if (Object.keys(classifierData).length > 0) {
            payload.classifier = { data: classifierDataToApi(classifierData) };
        }
    }

    return payload as NodeUpdate;
};

export const partialUpdateNode = async (
    diagram: string,
    node: string,
    data: any,
) => {
    const payload = toNodeUpdate(data);
    await updateNode(node, payload);

    invalidateDiagram(diagram);
    if (payload.classifier) {
        invalidateClassifiers();
    }
};

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export const deleteNode = async (_diagram: string, node: string) => {
    await deleteApiNode(node);

    // Deleting a node can also remove its classifier and relations
    queryClient.invalidateQueries();
};

export const addEdge = async (
    diagram: string,
    data: any,
    source: string,
    target: string,
) => {
    const { type, ...relationData } = data ?? {};

    await createEdge(diagram, {
        source_id: source,
        target_id: target,
        relation: {
            type,
            data: relationData,
        },
    } as EdgeCreate);

    invalidateDiagram(diagram);
};

// Old payloads looked like { rel: {...relation data}, data: {...edge data} }.
export const toEdgeUpdate = (data: any): EdgeUpdate => {
    const payload: Record<string, unknown> = {};

    if (data?.rel) {
        // Strip the fields we add on the frontend when reading edges
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        const { type, edge_data, relationId, ...relationData } = data.rel;
        payload.relation = { data: relationData };
    }

    for (const field of ["width", "color", "font", "rounded"]) {
        if (data?.data && field in data.data) {
            payload[field] = data.data[field];
        }
    }

    return payload as EdgeUpdate;
};

export const partialUpdateEdge = async (
    diagram: string,
    edge: string,
    data: any,
) => {
    // TODO(api): edge control points (position_handlers) can't be saved yet
    await updateEdge(edge, toEdgeUpdate(data));

    invalidateDiagram(diagram);
};

export const deleteEdge = async (diagram: string, edge: string) => {
    await deleteApiEdge(edge);

    invalidateDiagram(diagram);
};
