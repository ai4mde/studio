import { authAxios } from "$auth/state/auth";
import type {
    SystemOut,
    SystemCreate,
    SystemUpdate,
} from "../types/systems";

export const getSystems = async (
    projectId: string
): Promise<SystemOut[]> => {
    const { data } = await authAxios.get<SystemOut[]>(
        "/v1/metadata/systems/",
        {
            params: { project_id: projectId },
        }
    );

    return data;
};

export const getSystem = async (
    systemId: string
): Promise<SystemOut> => {
    const { data } = await authAxios.get<SystemOut>(
        `/v1/metadata/systems/${systemId}/`
    );

    return data;
};

export const createSystem = async (
    payload: SystemCreate
): Promise<SystemOut> => {
    const { data } = await authAxios.post<SystemOut>(
        "/v1/metadata/systems/",
        payload
    );

    return data;
};

export const updateSystem = async (
    systemId: string,
    payload: SystemUpdate
): Promise<SystemOut> => {
    const { data } = await authAxios.patch<SystemOut>(
        `/v1/metadata/systems/${systemId}/`,
        payload
    );

    return data;
};

export const deleteSystem = async (
    systemId: string
): Promise<void> => {
    await authAxios.delete(
        `/v1/metadata/systems/${systemId}/`
    );
};

export const exportSystems = async (
    systemIds: string[]
): Promise<unknown> => {
    const params = new URLSearchParams();

    systemIds.forEach((id) => {
        params.append("system_ids", id);
    });

    const { data } = await authAxios.get(
        "/v1/metadata/systems/export/",
        { params }
    );

    return data;
};