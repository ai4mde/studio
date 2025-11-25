import { deleteEdge } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";
import { useEditConnectionModal } from "$diagram/stores/modals";
import schema from "$diagram/types/edge.schema.json";
import { FormControl, FormLabel, Input, Option, Select } from "@mui/joy";
import Button from "@mui/joy/Button";
import { X } from "lucide-react";
import React, { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import Draggable from "react-draggable";
import style from "./editconnectionmodal.module.css";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { authAxios } from "$lib/features/auth/state/auth";

export const EditConnectionModal: React.FC = () => {
    const modalState = useEditConnectionModal();
    const { diagram, edges, type: diagramType } = useDiagramStore();

    const edge = useMemo(
        () => edges.find((e) => e.id == modalState.edge),
        [modalState.edge, edges],
    );

    const [object, setObject] = useState<any>(edge?.data ?? {});

    // --- helpers for schema inspection ---------------------------------------

    const getDiagramConst = (def: any): string | null => {
        return def?.properties?.diagram?.const ?? null;
    };

    const getTypeValue = (def: any): string | null => {
        const t = def?.properties?.type;
        if (!t) return null;
        if (t.const) return t.const;
        if (Array.isArray(t.enum) && t.enum.length > 0) return t.enum[0];
        return null;
    };

    // normalize diagram kind: default to "class" if unknown/empty
    const diagramKind: "class" | "activity" | "usecase" = (
        diagramType === "activity" || diagramType === "usecase"
    )
        ? (diagramType as "activity" | "usecase")
        : "class";

    // --- diagram-aware relation type list ------------------------------------

    const connectionTypes = useMemo(() => {
        const anyOf = schema.definitions.Edge.anyOf ?? [];

        if (diagramKind === "class") {
            const allowed = [
                "association",
                "composition",
                "generalization",
                "dependency",
            ];

            return anyOf.filter((def: any) => {
                const diagConst = getDiagramConst(def); // "class", "activity", "usecase" or null
                const t = getTypeValue(def); // "association", "composition", ...

                if (!t || !allowed.includes(t)) return false;
                // keep only edges that are for class diagrams or have no diagram at all (dependency)
                if (diagConst && diagConst !== "class") return false;

                return true;
            });
        }

        if (diagramKind === "activity") {
            return anyOf.filter(
                (def: any) => getDiagramConst(def) === "activity",
            );
        }

        if (diagramKind === "usecase") {
            return anyOf.filter(
                (def: any) => getDiagramConst(def) === "usecase",
            );
        }

        return [];
    }, [diagramKind]);

    // keep local object in sync with current edge
    useEffect(() => {
        setObject(edge?.data ?? {});
    }, [edge]);

    const relType = object?.type ?? null;
    const isAssociation = relType === "association";
    const isComposition = relType === "composition";
    const isDependency = relType === "dependency";
    const isGeneralization = relType === "generalization";
    const isAssocOrComp = isAssociation || isComposition;

    const queryClient = useQueryClient();

    const updateEdge = useMutation({
        mutationFn: async () => {
            await authAxios.patch(
                `/v1/diagram/${diagram}/edge/${edge?.id}/`,
                { rel: object },
            );
            queryClient.invalidateQueries({ queryKey: ["diagram"] });
        },
    });

    const onDelete = () => {
        modalState?.edge && deleteEdge(diagram, modalState.edge);
    };

    useEffect(() => {
        const down = (e: KeyboardEvent) => {
            if (e.key === "Escape") {
                modalState.close();
            }
        };

        document.addEventListener("keydown", down);
        return () => document.removeEventListener("keydown", down);
    });

    const nodeRef = React.useRef(null);

    return edge ? (
        createPortal(
            <div className={style.modal}>
                <div className={style.wrapper}>
                    <Draggable nodeRef={nodeRef} key={`edit-${edge.id}`}>
                        <div ref={nodeRef} className={style.main}>
                            <div className={style.head}>
                                <span className="p-2 px-3">
                                    Edit Connection (
                                    {edge.id.split("-").slice(-1)})
                                </span>
                                <button
                                    className="m-1 mx-2 rounded-sm"
                                    onClick={modalState.close}
                                >
                                    <X size={20} />
                                </button>
                            </div>

                            <div className="h-full overflow-y-scroll bg-white">
                                <div className={style.body}>
                                    {/* TYPE SELECT */}
                                    <FormControl size="sm">
                                        <FormLabel>Type</FormLabel>
                                        <Select
                                            placeholder="Select a connection type"
                                            value={relType}
                                            onChange={(_, value) => {
                                                setObject((obj: any) => ({
                                                    ...obj,
                                                    type: value,
                                                }));
                                            }}
                                        >
                                            {connectionTypes.map(
                                                (def: any, idx: number) => {
                                                    const t = getTypeValue(def);
                                                    return (
                                                        t && (
                                                            <Option
                                                                key={idx}
                                                                value={t}
                                                            >
                                                                {t}
                                                            </Option>
                                                        )
                                                    );
                                                },
                                            )}
                                        </Select>
                                    </FormControl>

                                    {/* ASSOCIATION / COMPOSITION FIELDS */}
                                    {isAssocOrComp && (
                                        <>
                                            <FormControl size="sm">
                                                <FormLabel>Label</FormLabel>
                                                <Input
                                                    value={object?.label ?? ""}
                                                    onChange={(e) => {
                                                        const value =
                                                            e.target.value;
                                                        setObject(
                                                            (obj: any) => ({
                                                                ...obj,
                                                                label: value,
                                                            }),
                                                        );
                                                    }}
                                                />
                                            </FormControl>

                                            <div className="flex w-full flex-row items-center justify-between gap-2">
                                                <FormControl size="sm">
                                                    <FormLabel>
                                                        Source Label
                                                    </FormLabel>
                                                    <Input
                                                        value={
                                                            object?.labels
                                                                ?.source ?? ""
                                                        }
                                                        onChange={(e) => {
                                                            const value =
                                                                e.target.value;
                                                            setObject(
                                                                (obj: any) => ({
                                                                    ...obj,
                                                                    labels: {
                                                                        ...(obj.labels ??
                                                                            {}),
                                                                        source:
                                                                            value,
                                                                    },
                                                                }),
                                                            );
                                                        }}
                                                    />
                                                </FormControl>
                                                <FormControl size="sm">
                                                    <FormLabel>
                                                        Target Label
                                                    </FormLabel>
                                                    <Input
                                                        value={
                                                            object?.labels
                                                                ?.target ?? ""
                                                        }
                                                        onChange={(e) => {
                                                            const value =
                                                                e.target.value;
                                                            setObject(
                                                                (obj: any) => ({
                                                                    ...obj,
                                                                    labels: {
                                                                        ...(obj.labels ??
                                                                            {}),
                                                                        target:
                                                                            value,
                                                                    },
                                                                }),
                                                            );
                                                        }}
                                                    />
                                                </FormControl>
                                            </div>

                                            <div className="flex w-full flex-row items-center justify-between gap-2">
                                                <FormControl size="sm">
                                                    <FormLabel>
                                                        Source Multiplicity
                                                    </FormLabel>
                                                    <Input
                                                        value={
                                                            object
                                                                ?.multiplicity
                                                                ?.source ?? ""
                                                        }
                                                        onChange={(e) => {
                                                            const value =
                                                                e.target.value;
                                                            setObject(
                                                                (obj: any) => ({
                                                                    ...obj,
                                                                    multiplicity:
                                                                        {
                                                                            ...(obj.multiplicity ??
                                                                                {}),
                                                                            source:
                                                                                value,
                                                                        },
                                                                }),
                                                            );
                                                        }}
                                                    />
                                                </FormControl>
                                                <FormControl size="sm">
                                                    <FormLabel>
                                                        Target Multiplicity
                                                    </FormLabel>
                                                    <Input
                                                        value={
                                                            object
                                                                ?.multiplicity
                                                                ?.target ?? ""
                                                        }
                                                        onChange={(e) => {
                                                            const value =
                                                                e.target.value;
                                                            setObject(
                                                                (obj: any) => ({
                                                                    ...obj,
                                                                    multiplicity:
                                                                        {
                                                                            ...(obj.multiplicity ??
                                                                                {}),
                                                                            target:
                                                                                value,
                                                                        },
                                                                }),
                                                            );
                                                        }}
                                                    />
                                                </FormControl>
                                            </div>
                                        </>
                                    )}

                                    {/* DEPENDENCY FIELDS */}
                                    {isDependency && (
                                        <FormControl size="sm">
                                            <FormLabel>Label</FormLabel>
                                            <Input
                                                value={object?.label ?? ""}
                                                onChange={(e) => {
                                                    const value =
                                                        e.target.value;
                                                    setObject((obj: any) => ({
                                                        ...obj,
                                                        label: value,
                                                    }));
                                                }}
                                            />
                                        </FormControl>
                                    )}

                                    {/* GENERALIZATION: no extra fields */}
                                    {isGeneralization && (
                                        <p className="text-xs text-gray-500 mt-2">
                                            Generalization has no additional
                                            editable properties.
                                        </p>
                                    )}
                                </div>
                            </div>

                            <div className={style.actions}>
                                <Button
                                    size="sm"
                                    onClick={() => updateEdge.mutate()}
                                    disabled={updateEdge.isPending}
                                >
                                    Save
                                </Button>
                                <Button
                                    color="danger"
                                    size="sm"
                                    onClick={() => onDelete()}
                                >
                                    Delete
                                </Button>
                            </div>
                        </div>
                    </Draggable>
                </div>
            </div>,
            document.body,
        )
    ) : (
        <></>
    );
};

export default EditConnectionModal;
