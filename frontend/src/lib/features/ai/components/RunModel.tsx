import { authAxios } from "$auth/state/auth";
import { queryClient } from "$shared/hooks/queryClient";
import { Button, Card, CircularProgress, Textarea } from "@mui/joy";
import { useMutation } from "@tanstack/react-query";
import { ArrowRight } from "lucide-react";
import React from "react";
import { Pipeline } from "../types";

type Props = {
    pipeline: Pipeline;
};

export const RunModel: React.FC<Props> = ({ pipeline }) => {
    const { mutate, isPending, isError, isSuccess } = useMutation({
        mutationFn: async () => {
            console.log("Running model:");
            await authAxios.post(`/v1/prose/pipelines/${pipeline.id}/run_model/`, {
                model: pipeline.url,
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
