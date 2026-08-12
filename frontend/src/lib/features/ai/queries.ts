import { authAxios } from "$auth/state/auth";
import { useQuery } from "@tanstack/react-query";
import { HitlRevisionHistoryResponse, Pipeline } from "./types";

export const usePipelines = () =>
    useQuery({
        queryKey: ["pipelines"],
        queryFn: async () => {
            const res = await authAxios.get<Pipeline[]>("/v1/prose/pipelines/");
            return res.data;
        },
    });

export const usePipeline = (pipelineId?: string) =>
    useQuery({
        queryKey: ["pipelines", pipelineId],
        queryFn: async () => {
            const res = await authAxios.get<Pipeline>(
                `/v1/prose/pipelines/${pipelineId}/`,
            );
            return res.data;
        },
        enabled: !!pipelineId,
    });

export const useSystemRevisions = (systemId?: string) =>
    useQuery({
        queryKey: ["system-revisions", systemId],
        queryFn: async () => {
            const res = await authAxios.get<HitlRevisionHistoryResponse>(
                `/v1/system-revisions/${systemId}`,
            );
            return res.data;
        },
        enabled: !!systemId,
    });
