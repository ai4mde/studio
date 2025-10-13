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
    const [newDiagramType, setNewDiagramType] = React.useState<string | null>(null);
    const [newDiagramName, setNewDiagramName] = React.useState("");
    const [createMode, setCreateMode] = React.useState(false);

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

    const { mutateAsync: addToDiagram, isPending, isError, isSuccess } = useMutation({
        mutationFn: async (targetDiagramId: string) => {
            const selectedClassifiers = _classifiers.filter((c) => classifiers.includes(c.id));
            const selectedRelations = _relations.filter((r) => relations.includes(r.id));
            console.log("addidng", {
                diagramId: targetDiagramId,
                classifierId: selectedClassifiers.map(c=>c.id),
                relationIds: selectedRelations.map(r=>r.id),
            });
            await authAxios.post(`/v1/prose/pipelines/${pipeline.id}/add_to_diagram/${targetDiagramId}/`, {
                pipeline_id: pipeline.id,
                diagram_id: targetDiagramId,
                classifiers: selectedClassifiers,
                relations: selectedRelations,
            });

            queryClient.invalidateQueries({ queryKey: ["pipelines"] });
        },
        onError: (e: any) => {
            console.error("add_to_diagram failed", e?.response?.status, e?.response?.data || e?.message);
        },
        onSuccess: () => {
            console.log("components added to diagram");
        }
    });

    const { mutateAsync: createDiagram, isPending: creatingDiagram} = useMutation({
        mutationFn: async ({ type, name }: { type: string, name: string }) => {
            const { data } = await authAxios.post("/v1/diagram/", {
                name,
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
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-1">

                    {/* Project */}
                    <div className="md:col-start-1 md:row-start-1">
                        <label className="block text-sm font-medium mb-1">Project</label>
                        <Select
                            size="md"
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
                    
                    {/* System */}
                    <div className="md:col-start-2 md:row-start-1">
                        <label className="block text-sm font-medium mb-1">System</label>
                        <Select
                            size="md"
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

                    {/* Diagram */}
                    <div className="md:col-start-3 md:row-start-1">
                        <label className="block text-sm font-medium mb-1">Diagram</label>
                        <Select
                            size="md"
                            className="w-full"
                            value = {diagram ?? null}
                            onChange={(_, val) => setDiagram(val ?? undefined)}
                        >
                            {project && system && (
                                <Option
                                    value="__new__"
                                    // Open submenu on hover
                                    onMouseEnter={(e) => {
                                        setSubmenuAnchorEl(e.currentTarget as HTMLElement);
                                        setSubmenuOpen(true);
                                    }}
                                    // Close submenu
                                    onMouseLeave={() => {setSubmenuOpen(false)}}
                                    // Prevent selecting this option
                                    onMouseDown={(e) => e.preventDefault()}
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
                                    onClick={() => {
                                        setSubmenuOpen(false);
                                        setCreateMode(true);
                                        setNewDiagramType(t.value);
                                        setNewDiagramName("");
                                    }}
                                >
                                    {t.label}
                                </MenuItem>
                            ))}
                        </Menu>

                        {/* Inline creation UI appears when createMode is on */}
                        {createMode && (
                            <div className="mt-2">
                                <label className="block text-sm font-medium mb-1">
                                    New Diagram Name
                                </label>
                                <input
                                    type="text"
                                    className="w-full border rounded px-2 py-1"
                                    placeholder="Enter a name..."
                                    value={newDiagramName}
                                    onChange={(e) => setNewDiagramName(e.target.value)}
                                />
                            </div>
                        )}
                    </div>

                    {/* Button */}
                    <div className="md:col-start-4 md:row-start-1">
                        <label className="block text-sm fpnt-medium mb-1 invisible" aria-hidden>
                            Action
                        </label>
                        <Button
                            size="md"
                            onClick={async () => {
                                let targetId = diagram;
                                if (createMode) {
                                    if (!newDiagramType || !newDiagramName.trim()) return;
                                    const created = await createDiagram({ type: newDiagramType, name: newDiagramName.trim() });
                                    targetId = String(created.id);
                                    setDiagram(targetId);
                                    setCreateMode(false);
                                }
                                if (targetId) {
                                    await addToDiagram(targetId);
                                }
                            }}
                            disabled={
                                !system ||
                                !project ||
                                (!createMode && !diagram) ||
                                (createMode && (!newDiagramType || !newDiagramName.trim())) ||
                                !classifiers.length ||
                                isPending ||
                                isSuccess ||
                                creatingDiagram
                            }
                        >
                            {isPending ? "Generating..."
                                : isSuccess ? "Successfully generated!"
                                : createMode ? "Create & add"
                                : "Add to diagram"
                            }
                        </Button>
                    </div>
                </div>
                {diagram === NEW_DIAGRAM && (
                    <div className="mt-2">
                        <label className="block text-xs font-medium mb-1">New diagram name</label>
                        <input
                            type="text"
                            className="w-full border rounded px-2 py-1"
                            placeholder="Enter a name..."
                            value={newDiagramName}
                            onChange={(e) => setNewDiagramName(e.target.value)}
                        />
                    </div>
                )}
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
