import { authAxios } from "$lib/features/auth/state/auth";
import { queryClient } from "$lib/shared/hooks/queryClient";

export const addNode = async (diagram: string, data: any) => {
    await authAxios.post(`/api/model/diagram/${diagram}/node/`, {
        type: data.type,
        data: data,
    });

    queryClient.invalidateQueries({
        queryKey: ["diagram", diagram],
    });
};

export const partialUpdateNode = async (
    diagram: string,
    node: string,
    data: any
) => {
    await authAxios.patch(`/api/model/diagram/${diagram}/node/${node}/`, data);

    queryClient.invalidateQueries({
        queryKey: ["diagram", diagram],
    });
};
export const deleteNode = async (diagram: string, node: string) => {
    await authAxios.delete(`/api/model/diagram/${diagram}/node/${node}/`);

    queryClient.invalidateQueries({
        queryKey: ["diagram", diagram],
    });
};

export const addEdge = async (diagram: string, data: any) => {
    await authAxios.post(`/api/model/diagram/${diagram}/edge/`, {
        type: data.type,
        data: data,
    });

    queryClient.invalidateQueries({
        queryKey: ["diagram", diagram],
    });
};

export const partialUpdateEdge = async (
    diagram: string,
    edge: string,
    data: any
) => {
    await authAxios.patch(`/api/model/diagram/${diagram}/edge/${edge}/`, data);

    queryClient.invalidateQueries({
        queryKey: ["diagram", diagram],
    });
};

export const deleteEdge = async (diagram: string, edge: string) => {
    await authAxios.delete(`/api/model/diagram/${diagram}/edge/${edge}/`);

    queryClient.invalidateQueries({
        queryKey: ["diagram", diagram],
    });
};
