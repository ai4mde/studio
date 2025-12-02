import { PreviewNode } from "$diagram/components/core/Node/Node";
import { addEdge } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";
import { useNewConnectionModal } from "$diagram/stores/modals";
import { queryClient } from "$shared/hooks/queryClient";
import { Alert, Button } from "@mui/joy";
import { X } from "lucide-react";
import React, { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import Draggable from "react-draggable";
import ClassConnectionFields, { isClassConnectionValid } from "../ConnectionFields/ClassConnectionFields";
import ActivityConnectionFields from "../ConnectionFields/ActivityConnectionFields";
import UseCaseConnectionFields from "../ConnectionFields/UseCaseConnectionFields";
import style from "./newconnectionmodal.module.css";

const isConnectionValid = (diagramType: string, o: any): boolean => {
    if (!o?.type) return false;

    if (diagramType === "classes" || diagramType === "class") {
        return isClassConnectionValid(o);
    }

    return true;
};

export const NewConnectionModal: React.FC = () => {
    const { nodes, diagram, type } = useDiagramStore();
    const { source, target, close } = useNewConnectionModal();

    // TODO: Figure out a way to do better form building
    // using the schema instead of pumping everything to
    // an any-typed object. Better yet, use the TypeScript
    // definition from ngUML.backend/model/specification
    // here. (ngUML.backend/issues/110)
    const [object, setObject] = useState<any>({});

    useEffect(() => {
        const down = (e: KeyboardEvent) => {
            e.key === "Escape" && close();
        };

        document.addEventListener("keydown", down);
        return () => document.removeEventListener("keydown", down);
    });

    const sourceNode = useMemo(
        () => nodes.find((e) => e.id === source),
        [nodes],
    );

    const targetNode = useMemo(
        () => nodes.find((e) => e.id === target),
        [nodes],
    );

    const nodeRef = React.useRef(null);

    return createPortal(
        <div className={style.modal}>
            <div className={style.wrapper}>
                <Draggable nodeRef={nodeRef}>
                    <form
                        ref={nodeRef}
                        className={style.main}
                        onSubmit={(e) => {
                            e.preventDefault();
                            diagram && source && object && target && addEdge(diagram, object, source, target);
                            queryClient.refetchQueries({
                                queryKey: ["diagram"],
                            });
                            close();
                        }}
                    >
                        <div className={style.head}>
                            <span className="p-2 px-3">
                                Connect
                                {` ${source?.split("-").slice(-1)}`} to
                                {` ${target?.split("-").slice(-1)}`}
                            </span>
                            <button
                                className="m-1 mx-2 rounded-sm"
                                onClick={close}
                            >
                                <X size={20} />
                            </button>
                        </div>
                        <div className={style.body}>
                            <Alert className="w-full">
                                <div className="flex w-full flex-row items-center justify-between">
                                    <span>Connecting</span>
                                    <div className="scale-75">
                                        {sourceNode && (
                                            // @ts-expect-error we should have a specific preview node
                                            <PreviewNode {...sourceNode} />
                                        )}
                                    </div>
                                    <span>to</span>
                                    <div className="scale-75">
                                        {targetNode && (
                                            // @ts-expect-error we should have a specific preview node
                                            <PreviewNode {...targetNode} />
                                        )}
                                    </div>
                                </div>
                            </Alert>
                            {type == "classes" || type == "class" ? (
                                <ClassConnectionFields
                                    object={object}
                                    setObject={setObject}
                                />
                            ) : null}
                            {type == "activity" ? (
                                <ActivityConnectionFields
                                    object={object}
                                    setObject={setObject}
                                />
                            ): null}
                            {type == "usecase" ? (
                                <UseCaseConnectionFields
                                    object={object}
                                    setObject={setObject}
                                />
                            ) : null}
                        </div>
                        <div className={style.actions}>
                            <Button
                                color="primary"
                                size="sm"
                                disabled={!isConnectionValid(type, object)}
                                type="submit"
                            >
                                Add
                            </Button>
                        </div>
                    </form>
                </Draggable>
            </div>
        </div>,
        document.body,
    );
};

export default NewConnectionModal;
