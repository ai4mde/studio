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

export const NewNodeModal: React.FC = () => {
    const { diagram, type, nodes, uniqueActors, relatedDiagrams } = useDiagramStore();
    const { close } = useNewNodeModal();

    // TODO: Figure out a way to do better form building
    // using the schema instead of pumping everything to
    // an any-typed object. Better yet, use the TypeScript
    // definition from ngUML.backend/model/specification
    // here. (ngUML.backend/issues/110)
    const [object, setObject] = useState<any>({});
    const queryClient = useQueryClient();

    useEffect(() => {
        const down = (e: KeyboardEvent) => {
            e.key === "Escape" && close();
        };

        document.addEventListener("keydown", down);
        return () => document.removeEventListener("keydown", down);
    });

    const swimlaneGroup = nodes.find((node) => node.type === 'swimlanegroup');
    const nodeRef = React.useRef(null);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        if (object.type !== 'swimlane') {
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
                                    setObject={setObject}
                                />
                            )}
                        </div>
                        <div className={style.actions}>
                            <Button
                                color="primary"
                                size="sm"
                                disabled={!object.type}
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

export default NewNodeModal;
