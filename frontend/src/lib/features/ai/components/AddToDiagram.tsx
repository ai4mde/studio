import { authAxios } from "$auth/state/auth";
import { PreviewNode } from "$diagram/components/core/Node/Node";
import { queryClient } from "$shared/hooks/queryClient";
import { Button, Card, Option, Select } from "@mui/joy";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowRight } from "lucide-react";
import React from "react";
import { Pipeline } from "../types";

type Props = {
    pipeline: Pipeline;
};

type ProjectOut = {
    id: string;
    name: string;
    description?: string;
};
type SystemOut = {
    id: string;
    name: string;
    description?: string;
};

type DiagramOut = {
    id: string;
    name: string;
    description?: string;
};

export const AddToDiagram: React.FC<Props> = ({ pipeline }) => {
    const [classifiers, setClassifiers] = React.useState<any[]>([]);
    const [relations, setRelations] = React.useState<any[]>([]);
    const [project, setProject] = React.useState<string | undefined>();
    const [system, setSystem] = React.useState<string | undefined>();
    const [diagram, setDiagram] = React.useState<string | undefined>();

    const projects = useQuery<ProjectOut[]>({
        queryKey: ["projects"],
        queryFn: async () => {
            return (await authAxios.get("/v1/metadata/projects/")).data;
        },
    });

    const systems = useQuery<SystemOut[]>({
        queryKey: ["systems", `${project}`],
        queryFn: async () => {
            return (
                await authAxios.get(`/v1/metadata/systems/`, {
                    params: {
                        project: project,
                    },
                })
            ).data;
        },
        enabled: !!project,
    });

    const diagrams = useQuery<DiagramOut[]>({
        queryKey: ["diagrams", `${project}`],
        queryFn: async () => {
            return (
                await authAxios.get(`/v1/diagram/system/${system}/`, {
                    params: {
                        system_id: system,
                    },
                })
            ).data;
        },
        enabled: !!system,
    });

    const _classifiers = pipeline?.output?.classifiers || [];
    const _relations = pipeline?.output?.relations || [];

    const toggleClassifier = (id: string) => {
        if (classifiers.includes(id)) {
            setClassifiers(classifiers.filter((c) => c !== id));
            setRelations(
                relations.filter((r) => {
                    const relation = _relations.find((rel: any) => rel.id == r);
                    return (
                        relation.data.source !== id &&
                        relation.data.target !== id
                    );
                }),
            );
        } else {
            setClassifiers([...classifiers, id]);
        }
    };

    const toggleRelation = (id: string, source: string, target: string) => {
        if (relations.includes(id)) {
            setRelations(relations.filter((c) => c !== id));
        } else {
            setRelations([...relations, id]);
            setClassifiers([...classifiers, source, target]);
        }
    };

    const { mutate, isPending, isError, isSuccess } = useMutation({
        mutationFn: async () => {
            const selectedClassifiers = _classifiers.filter((c) => classifiers.includes(c.id));
            const selectedRelations = _relations.filter((r) => relations.includes(r.id));
            await authAxios.post(`/v1/prose/pipelines/${pipeline.id}/add_to_diagram/${diagram}/`, {
                pipeline_id: pipeline.id,
                diagram_id: diagram,
                classifiers: selectedClassifiers,
                relations: selectedRelations,
            });

            queryClient.invalidateQueries({ queryKey: ["pipelines"] });
        },
    });

    return (
        <>
            <Card>
                <div className="flex w-full flex-row gap-4 p-1">
                    <Select
                        className="w-full"
                        onChange={(_, val) => setProject(`${val}`)}
                    >
                        {projects.isSuccess ? (
                            projects.data.map((p) => (
                                <Option value={p.id}>{p.name}</Option>
                            ))
                        ) : (
                            <Option value="loading" disabled>
                                Loading...
                            </Option>
                        )}
                    </Select>
                    <Select
                        className="w-full"
                        onChange={(_, val) => setSystem(`${val}`)}
                    >
                        {systems.isSuccess ? (
                            systems.data.map((p) => (
                                <Option value={p.id}>{p.name}</Option>
                            ))
                        ) : project ? (
                            <Option value="setproj" disabled>
                                Set a project first
                            </Option>
                        ) : (
                            <Option value="loading" disabled>
                                Loading...
                            </Option>
                        )}
                    </Select>
                    <Select
                        className="w-full"
                        onChange={(_, val) => setDiagram(`${val}`)}
                    >
                        {diagrams.isSuccess ? (
                            diagrams.data.length > 0 ? (
                                diagrams.data.map((p) => (
                                    <Option key={p.id} value={p.id}>
                                        {p.id}
                                    </Option>
                                ))
                            ) : (
                                <Option value="no-diagrams" disabled>
                                    Create a diagram first!
                                </Option>
                            )
                        ) : system ? (
                            <Option value="setsys" disabled>
                                Set a system first
                            </Option>
                        ) : (
                            <Option value="loading" disabled>
                                Loading...
                            </Option>
                        )}
                    </Select>
                    <Button
                        onClick={() => mutate()}
                        fullWidth
                        disabled={!system || !project || !diagram || !classifiers.length || isPending || isSuccess}
                    >
                        {isPending ? "Generating..."
                            : isSuccess ? "Successfully generated!"
                                : "Add to diagram"
                        }
                    </Button>
                </div>
            </Card>
            <Card className="flex w-full flex-col gap-4 p-4">
                <div className="flex w-full flex-col gap-1">
                    <span>Classifiers</span>
                    <div className="flex flex-row flex-wrap items-center gap-2">
                        {_classifiers.map((classifier: any) => (
                            <button
                                className={[
                                    "border p-1",
                                    classifiers.includes(classifier.id)
                                        ? "bg-blue-300 hover:bg-red-200"
                                        : "bg-stone-100 hover:bg-stone-200",
                                ].join(" ")}
                                onClick={() => toggleClassifier(classifier.id)}
                            >
                                <PreviewNode
                                    type={classifier.data.type}
                                    data={classifier.data}
                                    id={classifier.id}
                                    selected={false}
                                    zIndex={0}
                                    isConnectable={false}
                                    xPos={0}
                                    yPos={0}
                                    dragging={false}
                                />
                            </button>
                        ))}
                    </div>
                </div>
                <div className="flex w-full flex-col gap-1">
                    <span>Relations</span>
                    <div className="flex flex-row flex-wrap items-center gap-2">
                        {_relations.map((relation: any) => (
                            <span>
                                {[""].map(() => {
                                    const source = _classifiers.find(
                                        (e: any) =>
                                            e.id == relation.source,
                                    );
                                    const target = _classifiers.find(
                                        (e: any) =>
                                            e.id == relation.target,
                                    );

                                    if (!source || !target) {
                                        return <></>;
                                    }

                                    return (
                                        <button
                                            className={[
                                                "flex w-full flex-row items-center justify-between gap-2 border p-1",
                                                relations.includes(relation.id)
                                                    ? "bg-blue-300 hover:bg-red-200"
                                                    : "bg-stone-100 hover:bg-stone-200",
                                            ].join(" ")}
                                            onClick={() =>
                                                toggleRelation(
                                                    relation.id,
                                                    relation.source,
                                                    relation.target,
                                                )
                                            }
                                        >
                                            <span>
                                                {source && (
                                                    <PreviewNode
                                                        type={source?.data.type}
                                                        data={source?.data}
                                                        id={""}
                                                        selected={false}
                                                        zIndex={0}
                                                        isConnectable={false}
                                                        xPos={0}
                                                        yPos={0}
                                                        dragging={false}
                                                    />
                                                )}
                                            </span>
                                            {relation.data.multiplicity.source}
                                            <ArrowRight size={18} />
                                            {relation.data.type}
                                            <ArrowRight size={18} />
                                            {relation.data.multiplicity.target}
                                            <span>
                                                {target && (
                                                    <PreviewNode
                                                        type={target?.data.type}
                                                        data={target?.data}
                                                        id={""}
                                                        selected={false}
                                                        zIndex={0}
                                                        isConnectable={false}
                                                        xPos={0}
                                                        yPos={0}
                                                        dragging={false}
                                                    />
                                                )}
                                            </span>
                                        </button>
                                    );
                                })}
                            </span>
                        ))}
                    </div>
                </div>
            </Card>
        </>
    );
};
