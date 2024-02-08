import { authAxios } from "$auth/state/auth";
import { Button, Card, CircularProgress, Textarea } from "@mui/joy";
import React from "react";
import { Pipeline } from "../types";
import { useMutation } from "@tanstack/react-query";
import { queryClient } from "$shared/hooks/queryClient";
import axios from "axios";
import { ArrowRight } from "lucide-react";

type Props = {
    pipeline: Pipeline;
};

export const RunModel: React.FC<Props> = ({ pipeline }) => {
    const { mutate, isPending, isError, isSuccess } = useMutation({
        mutationFn: async () => {
            const res = await axios.get(pipeline.url, {
                params: {
                    requirements: pipeline.requirements,
                },
                withCredentials: false,
            });

            await authAxios.post(`/v1/prose/pipelines/${pipeline.id}/result/`, {
                output: res.data,
            });

            queryClient.invalidateQueries({ queryKey: ["pipelines"] });
        },
    });

    return (
        <div className="flex flex-col gap-4">
            <div className="flex flex-row items-center gap-2">
                <Textarea
                    value={pipeline.requirements}
                    disabled
                    className="w-full"
                    minRows={5}
                />
                <div className="w-fit">
                    <ArrowRight size={18} />
                </div>
                <Card className="flex h-full w-full flex-col items-center justify-center">
                    <span>{pipeline.url}</span>
                </Card>
            </div>
            <div className="flex w-full flex-row gap-1">
                <Button
                    onClick={() => mutate()}
                    fullWidth
                    color={
                        isSuccess ? "success" : isError ? "danger" : "primary"
                    }
                    disabled={isPending}
                >
                    {isPending ? <CircularProgress /> : "Run"}
                </Button>
            </div>
        </div>
    );
};
