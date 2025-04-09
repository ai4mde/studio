import { authAxios } from "$auth/state/auth";
import { queryClient } from "$shared/hooks/queryClient";
import { Button, Card } from "@mui/joy";
import { useMutation } from "@tanstack/react-query";
import React, { useState } from "react";
import { externalModels, models } from "../models";
import { Pipeline } from "../types";

type Props = {
    pipeline: Pipeline;
};

export const SelectModel: React.FC<Props> = ({ pipeline }) => {
    const [modelUrl, setModelUrl] = useState<string>("");

    const { mutate } = useMutation({
        mutationFn: async () => {
            await authAxios.post(`/v1/prose/pipelines/${pipeline.id}/model/`, {
                url: modelUrl,
                type: "metadata",
            });
            queryClient.invalidateQueries({ queryKey: ["pipelines"] });
        },
    });

    return (
        <div className="flex flex-col gap-2">
            <div className="flex flex-col gap-0">
                <span className="text-lg">Bucketing Models</span>
                <span className="text-sm">
                    Split requirements text into domain-specific segments
                </span>
            </div>
            <div className="flex flex-row flex-wrap gap-4 rounded-md bg-stone-50 p-4">
                {models
                    .filter((e) => e.type == "bucketing")
                    .map((e) => {
                        return (
                            <Card
                                onClick={() =>
                                    !e.disabled && setModelUrl(e.url)
                                }
                                color={
                                    e.disabled
                                        ? "neutral"
                                        : modelUrl == e.url
                                            ? "primary"
                                            : "neutral"
                                }
                                variant={
                                    e.disabled
                                        ? "soft"
                                        : modelUrl == e.url
                                            ? "solid"
                                            : "outlined"
                                }
                                className={
                                    e.disabled
                                        ? "select-none"
                                        : "cursor-pointer select-none"
                                }
                                sx={
                                    e.disabled
                                        ? {}
                                        : {
                                            "&:hover": {
                                                boxShadow: "md",
                                                borderColor:
                                                    "neutral.outlinedHoverBorder",
                                            },
                                        }
                                }
                                key={e.title}
                            >
                                <div className="flex flex-col gap-0 p-1">
                                    <span className="text-lg">
                                        {e.title} ({e.version})
                                    </span>
                                    <span className="text-xs">{e.author}</span>
                                </div>
                            </Card>
                        );
                    })}
            </div>
            <div className="flex flex-col gap-0">
                <span className="text-lg">NLP Text Transformation</span>
                <span className="text-sm">
                    Transform requirements text into metadata
                </span>
            </div>
            <div className="flex flex-row flex-wrap gap-4 rounded-md bg-stone-50 p-4">
                {models
                    .filter((e) => e.type == "metadata")
                    .map((e) => {
                        return (
                            <Card
                                onClick={() =>
                                    !e.disabled && setModelUrl(e.url)
                                }
                                color={
                                    e.disabled
                                        ? "neutral"
                                        : modelUrl == e.url
                                            ? "primary"
                                            : "neutral"
                                }
                                variant={
                                    e.disabled
                                        ? "soft"
                                        : modelUrl == e.url
                                            ? "solid"
                                            : "outlined"
                                }
                                className={
                                    e.disabled
                                        ? "select-none"
                                        : "cursor-pointer select-none"
                                }
                                sx={
                                    e.disabled
                                        ? {}
                                        : {
                                            "&:hover": {
                                                boxShadow: "md",
                                                borderColor:
                                                    "neutral.outlinedHoverBorder",
                                            },
                                        }
                                }
                                key={e.title}
                            >
                                <div className="flex flex-col gap-0 p-1">
                                    <span className="text-lg">
                                        {e.title} ({e.version})
                                    </span>
                                    <span className="text-xs">{e.author}</span>
                                </div>
                            </Card>
                        );
                    })}
            </div>
            <div className="flex flex-col gap-0">
                <span className="text-lg">External LLMs</span>
                <span className="text-sm">
                    Use external LLMs for parsing requirements
                </span>
            </div>
            <div className="flex flex-row flex-wrap gap-4 rounded-md bg-stone-50 p-4">
                {externalModels
                    .filter((e) => e.type == "metadata")
                    .map((e) => {
                        return (
                            <Card
                                onClick={() =>
                                    !e.disabled && setModelUrl(e.url)
                                }
                                color={
                                    e.disabled
                                        ? "neutral"
                                        : modelUrl == e.url
                                            ? "primary"
                                            : "neutral"
                                }
                                variant={
                                    e.disabled
                                        ? "soft"
                                        : modelUrl == e.url
                                            ? "solid"
                                            : "outlined"
                                }
                                className={
                                    e.disabled
                                        ? "select-none"
                                        : "cursor-pointer select-none"
                                }
                                sx={
                                    e.disabled
                                        ? {}
                                        : {
                                            "&:hover": {
                                                boxShadow: "md",
                                                borderColor:
                                                    "neutral.outlinedHoverBorder",
                                            },
                                        }
                                }
                                key={e.title}
                            >
                                <div className="flex flex-col gap-0 p-1">
                                    <span className="text-lg">
                                        {e.title} ({e.version})
                                    </span>
                                    <span className="text-xs">{e.author}</span>
                                </div>
                            </Card>
                        );
                    })}
            </div>
            <Button disabled={!modelUrl} onClick={() => mutate()}>
                Next
            </Button>
        </div>
    );
};
