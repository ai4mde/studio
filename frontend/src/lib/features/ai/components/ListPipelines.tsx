import React from "react";
import { usePipelines } from "../queries";
import { Card, CircularProgress } from "@mui/joy";
import { useMutation } from "@tanstack/react-query";
import { authAxios } from "$auth/state/auth";
import { queryClient } from "$shared/hooks/queryClient";
import { redirect } from "react-router";
import { Rocket, Workflow } from "lucide-react";

export const ListPipelines: React.FC = () => {
    const { data, isSuccess } = usePipelines();
    const { mutate } = useMutation({
        mutationFn: async () => {
            const res = await authAxios.post("/v1/prose/pipelines/");
            if (res.data) {
                queryClient.invalidateQueries({ queryKey: ["pipelines"] });
                redirect(`/build/${res.data.id}`);
            }
        },
    });

    if (!isSuccess) {
        return <CircularProgress />;
    }

    return (
        <div className="flex flex-row flex-wrap gap-4">
            {data.map((e) => {
                return (
                    <Card
                        component="a"
                        href={`/build/${e.id}`}
                        key={e.id}
                        className="group flex min-w-48 flex-col gap-2 p-0"
                    >
                        <div className="-m-4 mb-0 flex flex-row items-center justify-between gap-1 rounded-t-md bg-gray-600 p-3 text-lg font-bold text-stone-100 group-hover:bg-gray-500">
                            <Workflow />{" "}
                            <div className="flex flex-col text-right">
                                <span>Pipeline</span>
                                <span className="text-xs text-gray-400">
                                    {e.id.split("-").slice(-1)}
                                </span>
                            </div>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-sm">Created at</span>
                            <span className="text-xs">
                                {new Date(e.created_at).toLocaleDateString()}
                            </span>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-sm">Current Step</span>
                            <span className="flex flex-row gap-1 text-xs">
                                {e.step == 2 && (
                                    <span>Upload Requirements</span>
                                )}
                                {e.step == 3 && <span>Select Models</span>}
                                {e.step == 4 && <span>Run Models</span>}
                                {e.step == 5 && <span>Add to system</span>}
                                {e.step == 6 && <span>Complete</span>}
                                <span className="text-gray-400">
                                    ({e.step} / 6)
                                </span>
                            </span>
                        </div>
                    </Card>
                );
            })}
            <Card
                component="button"
                onClick={() => mutate()}
                color="success"
                variant="outlined"
            >
                <div className="flex h-full w-full min-w-16 flex-col items-center justify-center gap-2">
                    <Rocket />
                    <span>Create Pipeline</span>
                </div>
            </Card>
        </div>
    );
};
