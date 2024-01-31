import { authAxios } from "$auth/state/auth";
import { useQuery } from "@tanstack/react-query";
import { Pipeline } from "./types";

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
