import { authAxios } from "$auth/state/auth";
import {
    Button,
    FormControl,
    FormHelperText,
    FormLabel,
    Textarea,
} from "@mui/joy";
import React from "react";
import { Pipeline } from "../types";
import { useMutation } from "@tanstack/react-query";
import { queryClient } from "$shared/hooks/queryClient";

type Props = {
    pipeline: Pipeline;
};

export const UploadRequirements: React.FC<Props> = ({ pipeline }) => {
    const { mutate } = useMutation({
        mutationFn: async (requirements: string) => {
            await authAxios.post(
                `/v1/prose/pipelines/${pipeline.id}/requirements/`,
                {
                    requirements: requirements,
                },
            );

            queryClient.invalidateQueries({ queryKey: ["pipelines"] });
        },
    });

    return (
        <form
            className="flex w-full flex-col gap-2"
            onSubmit={(e) => {
                e.preventDefault();
                const requirements = new FormData(e.currentTarget).get(
                    "requirements",
                );
                if (requirements) mutate(requirements.toString());
            }}
        >
            <FormControl>
                <FormLabel>Requirements</FormLabel>
                <Textarea
                    minRows="12"
                    name="requirements"
                    required
                    defaultValue={pipeline.requirements}
                />
                <FormHelperText>
                    Enter your requirements text here.
                </FormHelperText>
            </FormControl>
            <Button type="submit" color="primary">
                Submit
            </Button>
        </form>
    );
};
