import { addNode, partialUpdateNode } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";
import { useNewNodeModal } from "$diagram/stores/modals";
import Button from "@mui/joy/Button";
import { X } from "lucide-react";
import React, { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import Draggable from "react-draggable";
import { NewActivityNode } from "./NewActivityNode";
import { NewClassNode } from "./NewClassNode";
import { NewUsecaseNode } from "./NewUsecaseNode";
import { NewComponentNode } from "./NewComponentNode"
import style from "./newnodemodal.module.css";
import { listClassifiers, classifierNameExists } from "../../../../../../api/metadata/classifier";
import { useClassifiers } from "../../../../../../api/metadata/hooks/classifier";
import type { ClassifierRead } from "../../../../../../api/metadata/classifier";

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

    const {
        data: classifiers = [],
        isFetching: checkingName,
        isError: classifierLoadError,
    } = useClassifiers(
        { system_id: systemId || undefined },
        !!systemId,
    );

    // TODO: Figure out a way to do better form building
    // using the schema instead of pumping everything to
    // an any-typed object. Better yet, use the TypeScript
    // definition from ngUML.backend/model/specification
    // here. (ngUML.backend/issues/110)
    const [object, setObject] = useState<any>({});

    const name = (object?.name ?? "").trim();

    const nameError =
        UNIQUE_NAME_TYPES.has(object?.type) &&
        name &&
        !classifierLoadError &&
        classifierNameExists(
            classifiers,
            name,
            object.type as ClassifierRead["type"],
        )
            ? `A classifier named "${name}" already exists in this system.`
            : "";

    useEffect(() => {
        const down = (e: KeyboardEvent) => {
            e.key === "Escape" && close();
        };

        document.addEventListener("keydown", down);
        return () => document.removeEventListener("keydown", down);
    });

    const swimlaneGroup = nodes.find((node) => node.type === 'swimlanegroup');
    const systemBoundaryExists = nodes.some((node) => node.type === 'system_boundary');
    // Take the system classifiers straight from the system, so systems that
    // aren't drawn in a diagram yet can be picked too
    const systemNodes = classifiers
        .filter((classifier) => classifier.type === "system" && !!classifier.id)
        .map((classifier) => ({
            id: classifier.id!,
            name: (classifier.data as { name?: string }).name ?? "",
            type: classifier.type,
            cls: classifier.id!,
        }));
    const nodeRef = React.useRef(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (checkingName) return;
        if (nameError) return;

        // 1) Swimlane special case: create/update swimlanegroup
        // TODO(api): "swimlanegroup" is not a classifier type in the new backend,
        // swimlanes are now separate classifiers with a parent, so this still fails
        // See Maarten's explanation
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

            close();
            return;
        }

        // 2) Optional uniqueness check (only for types that must be unique)
        if (UNIQUE_NAME_TYPES.has(object?.type) && name && systemId) {
            const latestClassifiers = await listClassifiers({
                system_id: systemId,
            });

            if (
                classifierNameExists(
                    latestClassifiers,
                    name,
                    object.type as ClassifierRead["type"],
                )
            ) {
                return;
            }
}

        // 3) Create all non-swimlane nodes (object/event allowed to repeat)
        addNode(diagram, object);
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
                                            .filter((diagram) => diagram.type === 'class')
                                            .flatMap((diagram) => diagram.nodes.filter((node) => node.type === "class"))
                                            .map((node) => node.name)
                                    }
                                />
                            )}
                            {type == "class" && (
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
