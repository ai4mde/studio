import { addNode, partialUpdateNode } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";
import { useNewNodeModal } from "$diagram/stores/modals";
import Button from "@mui/joy/Button";
import { useQueryClient } from "@tanstack/react-query";
import { X } from "lucide-react";
import React, { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import Draggable from "react-draggable";
import { NewActivityNode } from "./NewActivityNode";
import { NewClassNode } from "./NewClassNode";
import { NewUsecaseNode } from "./NewUsecaseNode";
import style from "./newnodemodal.module.css";
import { authAxios } from "$lib/features/auth/state/auth";

export const NewNodeModal: React.FC = () => {
    const { diagram, type, nodes, uniqueActors, relatedDiagrams, systemId } = useDiagramStore();
    const { close } = useNewNodeModal();

    // TODO: Figure out a way to do better form building
    // using the schema instead of pumping everything to
    // an any-typed object. Better yet, use the TypeScript
    // definition from ngUML.backend/model/specification
    // here. (ngUML.backend/issues/110)
    const [object, setObject] = useState<any>({});
    const [nameError, setNameError] = useState<string>("");
    const [checkingName, setCheckingName] = useState(false);
    const [lastCheckedName, setLastCheckedName] = useState("");

    const queryClient = useQueryClient();

    useEffect(() => {
        const down = (e: KeyboardEvent) => {
            e.key === "Escape" && close();
        };

        document.addEventListener("keydown", down);
        return () => document.removeEventListener("keydown", down);
    });

    useEffect(() => {
        // Only validate "normal" nodes that have a name
        if (object?.type === "swimlane") {
            setNameError("");
            setCheckingName(false);
            return;
        }

        const name = (object?.name ?? "").trim();
        const ctype = object?.type;

        // No name yet -> no error, button should be enabled (assuming object.type exists)
        if (!name || !systemId || !ctype) {
            setNameError("");
            setCheckingName(false);
            return;
        }

        // Optional: avoid re-checking the exact same name repeatedly
        if (name === lastCheckedName) return;

        let cancelled = false;
        setCheckingName(true);

        const t = window.setTimeout(async () => {
            try {
                const res = await authAxios.get(
                    `/v1/metadata/systems/${systemId}/classifiers/exists/`,
                    { params: { name, ctype } },
                );

                if (cancelled) return;

                setLastCheckedName(name);

                if (res.data?.exists) {
                    setNameError(`A classifier named "${name}" already exists in this system.`);
                } else {
                    setNameError("");
                }
            } catch {
                if (!cancelled) {
                    // fail open: don’t block creation on temporary network error
                    setNameError("");
                }
            } finally {
                if (!cancelled) setCheckingName(false);
            }
        }, 250); // debounce

        return () => {
            cancelled = true;
            window.clearTimeout(t);
        };
    }, [object?.name, object?.type, systemId]);


    const swimlaneGroup = nodes.find((node) => node.type === 'swimlanegroup');
    const systemBoundaryExists = nodes.some((node) => node.type === 'system_boundary');
    const nodeRef = React.useRef(null);
    const missingControlSubtype = object.type === "control" && !object.subtype;
    const missingSwimlaneActor = object.type === "swimlane" && (!object.swimlanes || object.swimlanes.length === 0);
    const missingObjectClass = object.type === "object" && !object.class;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (checkingName) return;
        if (nameError) return;

        setNameError("");

        if (object.type === "swimlane" && (!object.swimlanes || object.swimlanes.length === 0)) return;
        if (object.type === "object" && !object.class) return;
        if (object.type === "control" && !object.subtype) return;

        if (object.type !== 'swimlane') {
            if (object?.name && systemId) {
                const res = await authAxios.get(
                    `/v1/metadata/systems/${systemId}/classifiers/exists/`,
                    { params: { name: object.name, ctype: object.type } },
                );

                if (res.data?.exists) {
                    setNameError(`A classifier named "${object.name}" already exists in this system.`);
                    return;
                }
            }

            addNode(diagram, object);
        } else {
            const { height, width, horizontal, swimlanes } = object;
            if (swimlaneGroup) {
                partialUpdateNode(
                    diagram,
                    swimlaneGroup.id,
                    {
                        cls: {
                            swimlanes: [...swimlaneGroup.data.swimlanes, ...swimlanes],
                        }
                    }
                )
            } else {
                addNode(
                    diagram,
                    {
                        type: 'swimlanegroup',
                        role: 'swimlane',
                        swimlanes: swimlanes,
                        height,
                        width,
                        horizontal
                    }
                );
            }
        }
        queryClient.refetchQueries({
            queryKey: ["diagram"],
        });
        close();
    };

    return createPortal(
        <div className={style.modal}>
            <div className={style.wrapper}>
                <Draggable nodeRef={nodeRef}>
                    <form
                        ref={nodeRef}
                        className={style.main}
                        onSubmit={handleSubmit}
                    >
                        <div className={style.head}>
                            <span className="p-2 px-3">
                                Add Node to Diagram
                            </span>
                            <button
                                className="m-1 mx-2 rounded-sm"
                                onClick={close}
                                type="button"
                            >
                                <X size={20} />
                            </button>
                        </div>
                        <div className={style.body}>
                            {type == "activity" && (
                                <NewActivityNode
                                    object={object}
                                    uniqueActors={uniqueActors}
                                    existingActors={
                                        swimlaneGroup
                                            ? swimlaneGroup.data.swimlanes.map((swimlane) => swimlane.actorNodeName || "")
                                            : []
                                    }
                                    swimlaneGroupExists={!!swimlaneGroup}
                                    setObject={setObject}
                                    classes={
                                        relatedDiagrams
                                            .filter((diagram) => diagram.type === 'classes')
                                            .flatMap((diagram) => diagram.nodes.map((node) => node.name))
                                    }
                                />
                            )}
                            {type == "classes" && (
                                <NewClassNode
                                    object={object}
                                    setObject={setObject}
                                />
                            )}
                            {type == "usecase" && (
                                <NewUsecaseNode
                                    object={object}
                                    systemBoundaryExists={systemBoundaryExists}
                                    setObject={setObject}
                                />
                            )}
                        </div>
                        <div className={style.actions}>
                            <div style={{ minHeight: 18 }}>
                                {nameError && (
                                    <div style={{ fontSize: 12, color: "#b42318" }}>
                                        {nameError}
                                    </div>
                                )}
                            </div>

                            <Button
                                color="primary"
                                size="sm"
                                disabled={!object.type || missingControlSubtype || missingSwimlaneActor || missingObjectClass || !!nameError || checkingName}
                                type="submit"
                            >
                                {checkingName ? "Checking..." : "Add"}
                            </Button>
                        </div>
                    </form>
                </Draggable>
            </div>
        </div>,
        document.body,
    );
};

export default NewNodeModal;
