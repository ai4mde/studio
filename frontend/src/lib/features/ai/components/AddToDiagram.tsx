import { authAxios } from "$auth/state/auth";
import { PreviewNode } from "$diagram/components/core/Node/Node";
import { queryClient } from "$shared/hooks/queryClient";
import { Button, Card, Option, Select, Menu, MenuItem } from "@mui/joy";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowRight, Plus } from "lucide-react";
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

const NEW_DIAGRAM = "__new_diagram__";

const DIAGRAM_TYPES = [
    {value: "classes", label: "Class"},
    {value: "usecase", label: "Use Case"},
    {value: "activity", label: "Activity"},
    {value: "component", label: "Component"},
];

export const AddToDiagram: React.FC<Props> = ({ pipeline }) => {
    const [classifiers, setClassifiers] = React.useState<any[]>([]);
    const [relations, setRelations] = React.useState<any[]>([]);
    const [project, setProject] = React.useState<string | undefined>();
    const [system, setSystem] = React.useState<string | undefined>();
    const [diagram, setDiagram] = React.useState<string | undefined>();
    const [submenuAnchorEl, setSubmenuAnchorEl] = React.useState<HTMLElement | null>(null);
    const [submenuOpen, setSubmenuOpen] = React.useState(false);

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

    const { mutateAsync: createDiagram, isPending: creatingDiagram} = useMutation({
        mutationFn: async ({ type }: { type: string}) => {
            const { data } = await authAxios.post("/v1/diagram/", {
                name: "Untitled diagram",
                system,
                type
            });
            return data;
        },
        onSuccess: async (data) => {
            queryClient.setQueryData<DiagramOut[]>(
                ["diagrams", `${project}`],
                (old) => {
                    const prev = Array.isArray(old) ? old : [];
                    if (prev.some(d => String(d.id) === String(data.id))) return prev;
                    return [{ id: String(data.id), name: data.name ?? "Untitled diagram" }, ...prev];
                }
            );
            // Select new diagram
            setDiagram(String(data.id));
            // Refresh list so new diagram appears in dropdown
            await queryClient.invalidateQueries({ queryKey: ["diagrams", `${project}`] });
        }
    });

    return (
        <>
            <Card>
                <div className="flex w-full flex-row gap-4 p-1 items-end">
                    <div className="w-full">
                        <label className="block text-sm font-medium mb-1">Project</label>
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
                    </div>
                    <div className="w-full">
                        <label className="block text-sm font-medium mb-1">System</label>
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
                    </div>
                    <div className="w-full">
                        <label className="block text-sm font-medium mb-1">Diagram</label>
                        <Select
                            className="w-full"
                            value = {diagram ?? null}
                            onChange={async (_e, val) => {
                                const raw = val && typeof val === "object" ? (val as any).value : val;
                                if (raw === NEW_DIAGRAM) {
                                    return;
                                }
                                if (raw == null) {
                                    setDiagram(undefined);
                                    return;
                                }
                                setDiagram(String(raw));
                            }}
                            renderValue={(selected) => {
                                if (!selected) return null;
                                const raw =
                                    typeof selected === "string" || typeof selected === "number"
                                        ? String(selected)
                                        : (selected as any)?.value ?? "";
                                if (!raw) return null;
                                const d = diagrams.data?.find((x) => String(x.id) === raw);
                                if (d) return d.name;
                                if (typeof selected === "object" && (selected as any)?.label)
                                    return (selected as any).label;
                                return raw;
                            }}
                        >
                            {project && system && (
                                <Option
                                key="__new__" 
                                value={NEW_DIAGRAM}
                                // Open submenu on hover
                                onMouseEnter={(e) => {
                                    setSubmenuAnchorEl(e.currentTarget as HTMLElement);
                                    setSubmenuOpen(true);
                                }}
                                onMouseLeave={() => {
                                    setSubmenuOpen(false);
                                }}
                                // Prevent selecting this option
                                onClick={(e) => e.preventDefault()}
                                >
                                    <span className="flex items-center">
                                        <Plus size={16} className="inline mr-1" />
                                        New Diagram...
                                        <span className="ml-auto">▸</span>
                                    </span>
                                </Option>
                            )}
                            {diagrams.isSuccess ? (
                                diagrams.data.length > 0 ? (
                                    diagrams.data.map((p) => (
                                        <Option key={p.id} value={String(p.id)}>
                                            {p.name}
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
                        <Menu
                            open={submenuOpen}
                            anchorEl={submenuAnchorEl}
                            onClose={() => setSubmenuOpen(false)}
                            placement="right-start"
                            variant="outlined"
                            size="sm"
                            sx={{ zIndex: 1300 }}
                            onMouseEnter={() => setSubmenuOpen(true)}
                            onMouseLeave={() => setSubmenuOpen(false)}
                        >
                            {DIAGRAM_TYPES.map(t => (
                                <MenuItem
                                    key={t.value}
                                    onClick={async () => {
                                        setSubmenuOpen(false);
                                        await createDiagram({ type: t.value });
                                    }}
                                >
                                    {t.label}
                                </MenuItem>
                            ))}
                        </Menu>
                    </div>
                    <div className="w-full">
                        <Button
                            onClick={() => mutate()}
                            fullWidth
                            disabled={!system || !project || !diagram || diagram === NEW_DIAGRAM || !classifiers.length || isPending || isSuccess || creatingDiagram}
                        >
                            {isPending ? "Generating..."
                                : isSuccess ? "Successfully generated!"
                                    : "Add to diagram"
                            }
                        </Button>
                    </div>
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
