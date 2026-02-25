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
import { NewComponentNode } from "./NewComponentNode"
import style from "./newnodemodal.module.css";
import { authAxios } from "$lib/features/auth/state/auth";

export const NewNodeModal: React.FC = () => {
    const UNIQUE_NAME_TYPES = new Set([
        "class",
        "enum",
        "signal",
        "action",
        "actor",
        "usecase",
    ]);

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
        const isNameType = UNIQUE_NAME_TYPES.has(object?.type);

        if (!isNameType) {
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
    const systemNodes = relatedDiagrams
        .flatMap(diagram => diagram.nodes ?? [])
        .filter(node => node?.type === "system");
    const nodeRef = React.useRef(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (checkingName) return;
        if (nameError) return;

        setNameError("");

        // 1) Swimlane special case: create/update swimlanegroup
        if (object.type === "swimlane") {
            const { height, width, horizontal, swimlanes } = object;

            if (!swimlanes || swimlanes.length === 0) return;

            if (swimlaneGroup) {
                partialUpdateNode(diagram, swimlaneGroup.id, {
                    cls: {
                        swimlanes: [...swimlaneGroup.data.swimlanes, ...swimlanes],
                    },
                });
            } else {
                addNode(diagram, {
                    type: "swimlanegroup",
                    swimlanes,
                    height,
                    width,
                    horizontal,
                });
            }

            queryClient.refetchQueries({ queryKey: ["diagram"] });
            close();
            return;
        }

        // 2) Optional uniqueness check (only for types that must be unique)
        if (UNIQUE_NAME_TYPES.has(object?.type)) {
            const name = (object?.name ?? "").trim();
            if (name && systemId) {
                const res = await authAxios.get(
                    `/v1/metadata/systems/${systemId}/classifiers/exists/`,
                    { params: { name, ctype: object.type } },
                );

                if (res.data?.exists) {
                    setNameError(`A ${object.type} named "${name}" already exists in this system.`);
                    return;
                }
            }
        }

        // 3) Create all non-swimlane nodes (object/event allowed to repeat)
        addNode(diagram, object);

        queryClient.refetchQueries({ queryKey: ["diagram"] });
        close();
    };

    const isAction = object?.type === "action";
    const isSwimlane = object?.type === "swimlane";
    const isObject = object?.type === "object";
    const isEvent = object?.type === "event";

    // Action nodes: name required
    const missingActionName = isAction && !(object?.name ?? "").trim();

    // Swimlane: actor required
    const missingSwimlaneActors =
        isSwimlane && (!object?.swimlanes || object.swimlanes.length === 0);

    // Object/Event: cls/signal required
    const missingObjectCls = isObject && !object?.cls;
    const missingEventSignal = isEvent && !object?.signal;

    // Control: type required
    const missingType = object?.role === "control" && !object?.type;

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
                                    systemNodes={systemNodes}
                                    setObject={setObject}
                                />
                            )}
                            {type == "component" && (
                                <NewComponentNode
                                    object={object}
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
                                disabled={
                                    !object.type ||
                                    !!nameError ||
                                    checkingName ||
                                    missingActionName ||
                                    missingSwimlaneActors ||
                                    missingObjectCls ||
                                    missingEventSignal ||
                                    missingType
                                }
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
