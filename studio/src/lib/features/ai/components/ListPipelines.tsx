import React from "react";
import { usePipelines } from "../queries";
import { Card, CircularProgress } from "@mui/joy";
import { useMutation } from "@tanstack/react-query";
import { authAxios } from "$auth/state/auth";
import { queryClient } from "$shared/hooks/queryClient";
import { redirect } from "react-router";

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
                        className="flex flex-col gap-2"
                    >
                        <div className="text-lg font-bold">
                            {e.type} pipeline
                        </div>
                        <div className="text-sm">{e.created_at}</div>
                        <div className="text-sm">
                            {e.id.split("-").slice(-1)}
                        </div>
                    </Card>
                );
            })}
            <Card component="button" onClick={() => mutate()}>
                <div className="text-lg font-bold">New pipeline</div>
                <div className="text-sm">-</div>
                <div className="text-sm">-</div>
            </Card>
        </div>
    );
};
