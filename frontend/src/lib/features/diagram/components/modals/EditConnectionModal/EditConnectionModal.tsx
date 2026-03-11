import { deleteEdge } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";
import { useEditConnectionModal } from "$diagram/stores/modals";
import Button from "@mui/joy/Button";
import { X } from "lucide-react";
import React, { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import Draggable from "react-draggable";
import style from "./editconnectionmodal.module.css";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { authAxios } from "$lib/features/auth/state/auth";

import ClassConnectionFields, { isClassConnectionValid } from "../ConnectionFields/ClassConnectionFields";
import ActivityConnectionFields from "../ConnectionFields/ActivityConnectionFields";
import UseCaseConnectionFields from "../ConnectionFields/UseCaseConnectionFields";

export const EditConnectionModal: React.FC = () => {
    const modalState = useEditConnectionModal();
    const { diagram, edges, type } = useDiagramStore();

    const edge = useMemo(
        () => edges.find((e) => e.id == modalState.edge),
        [modalState.edge, edges],
    );

    const [object, setObject] = useState<any>(edge?.data ?? {});

    useEffect(() => {
        setObject(edge?.data ?? {});
    }, [edge]);

    const queryClient = useQueryClient();

    const updateEdge = useMutation({
        mutationFn: async () => {
            const rel =
                type === "activity"
                    ? { ...object, type: "controlflow", isDirected: object?.isDirected ?? true }
                    : object;

            await authAxios.patch(
                `/v1/diagram/${diagram}/edge/${edge?.id}/`,
                { rel },
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

    const isValid = () => {
        // Classes: must pass class validation (requires type)
        if (type === "classes" || type === "class") {
            return isClassConnectionValid(object);
        }

        // Usecase: type is required
        if (type === "usecase") {
            return !!object?.type;
        }

        // Activity: type is implicit, no dropdown, always valid
        if (type === "activity") {
            return true;
        }

        // Default fallback
        return true;
    };

    if (!edge) {
        return <></>;
    }

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

                            <div className="h-full overfull-y-scroll bg-white">
                                <div className={style.body}>
                                    {type === "classes" && (
                                        <ClassConnectionFields
                                            object={object}
                                            setObject={setObject}
                                        />
                                    )}
                                    {type === "activity" && (
                                        <ActivityConnectionFields
                                            object={object}
                                            setObject={setObject}
                                            hideGuard={!!object?.condition}
                                        />
                                    )}
                                    {type === "usecase" && (
                                        <UseCaseConnectionFields
                                            object={object}
                                            setObject={setObject}
                                        />
                                    )}
                                </div>
                            </div>

                            <div className={style.actions}>
                                <Button
                                    size="sm"
                                    onClick={() => isValid() && updateEdge.mutate()}
                                    disabled={!isValid() || updateEdge.isPending}
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
