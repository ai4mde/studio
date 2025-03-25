import { authAxios } from "$lib/features/auth/state/auth";
import { queryClient } from "$lib/shared/hooks/queryClient";

export const addNode = async (diagram: string, data: any) => {
    await authAxios.post(`/v1/diagram/${diagram}/node/`, {
        cls: data,
    });

    queryClient.invalidateQueries({
        queryKey: ["diagram", diagram],
    });
};

export const importNode = async (diagram: string, id: string) => {
    await authAxios.post(`/v1/diagram/${diagram}/node/import/${id}/`, {
    });

    queryClient.invalidateQueries({
        queryKey: ["diagram", diagram],
    });
};

export const partialUpdateNode = async (
    diagram: string,
    node: string,
    data: any,
) => {
    await authAxios.patch(`/v1/diagram/${diagram}/node/${node}/`, data);

    queryClient.invalidateQueries({
        queryKey: ["diagram", diagram],
    });
};
export const deleteNode = async (diagram: string, node: string) => {
    await authAxios.delete(`/v1/diagram/${diagram}/node/${node}/`);

    queryClient.invalidateQueries({
        queryKey: ["diagram", diagram],
    });
};

export const addEdge = async (
    diagram: string,
    data: any,
    source: string,
    target: string,
) => {
    await authAxios.post(`/v1/diagram/${diagram}/edge/`, {
        source: source,
        target: target,
        rel: data,
    });

    queryClient.invalidateQueries({
        queryKey: ["diagram", diagram],
    });
};

export const partialUpdateEdge = async (
    diagram: string,
    edge: string,
    data: any,
) => {
    await authAxios.patch(`/v1/diagram/${diagram}/edge/${edge}/`, data);

    queryClient.invalidateQueries({
        queryKey: ["diagram", diagram],
    });
};

export const deleteEdge = async (diagram: string, edge: string) => {
    await authAxios.delete(`/v1/diagram/${diagram}/edge/${edge}/`);

    queryClient.invalidateQueries({
        queryKey: ["diagram", diagram],
    });
};
