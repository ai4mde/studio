import { authAxios } from "$auth/state/auth";
import {
    Button,
    FormControl,
    FormHelperText,
    FormLabel,
    Input,
    Textarea,
    Card,
    CircularProgress,
} from "@mui/joy";
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
    const { mutate, isPending, isError, isSuccess, data } = useMutation({
        mutationFn: async () => {
            const res = await axios.get(pipeline.url, {
                params: {
                    requirements: pipeline.requirements,
                },
                withCredentials: false,
            });
            return res.data;
        },
    });

    const [classifiers, setClassifiers] = React.useState<any[]>([]);
    const [relations, setRelations] = React.useState<any[]>([]);

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
            <Button
                onClick={() => mutate()}
                disabled={isPending}
                color={isSuccess ? "success" : isError ? "danger" : "primary"}
            >
                {isPending ? <CircularProgress /> : "Run"}
            </Button>
            {isSuccess ? (
                <Card className="flex w-full flex-col gap-4 p-4">
                    <span>Select Results</span>
                    <div className="flex w-full flex-col">
                        {data.classifiers.map((classifier: any) => (
                            <div className="flex flex-row items-center gap-2">
                                <input
                                    type="checkbox"
                                    checked={classifiers.includes(
                                        classifier.id,
                                    )}
                                    onChange={(e) => {
                                        if (e.target.checked) {
                                            setClassifiers([
                                                ...classifiers,
                                                classifier.id,
                                            ]);
                                        } else {
                                            setClassifiers(
                                                classifiers.filter(
                                                    (c) => c !== classifier.id,
                                                ),
                                            );
                                        }
                                    }}
                                />
                                <span>{classifier.data?.name}</span>
                            </div>
                        ))}
                    </div>
                    <div className="flex w-full flex-col">
                        {data.relations.map((relation: any) => (
                            <div className="flex flex-row items-center gap-2">
                                <input
                                    type="checkbox"
                                    checked={relations.includes(relation.id)}
                                    onChange={(e) => {
                                        if (e.target.checked) {
                                            setRelations([
                                                ...relations,
                                                relation.id,
                                            ]);
                                        } else {
                                            setRelations(
                                                relations.filter(
                                                    (c) => c !== relation.id,
                                                ),
                                            );
                                        }
                                    }}
                                />
                                <span>{relation.name}</span>
                            </div>
                        ))}
                    </div>
                </Card>
            ) : (
                <Card className="w-full p-4 text-center">
                    Run pipeline first
                </Card>
            )}
        </div>
    );
};
