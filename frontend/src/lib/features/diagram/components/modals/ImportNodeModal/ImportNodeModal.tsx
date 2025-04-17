import { importNode } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";
import { useImportNodeModal } from "$diagram/stores/modals";
import Button from "@mui/joy/Button";
import { useQueryClient } from "@tanstack/react-query";
import { X } from "lucide-react";
import React, { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import Draggable from "react-draggable";
import { ImportActivityNode } from "./ImportActivityNode";
import { ImportClassNode } from "./ImportClassNode";
import { ImportUsecaseNode } from "./ImportUsecaseNode";
import style from "./importnodemodal.module.css";

export const ImportNodeModal: React.FC = () => {
    const { diagram, type } = useDiagramStore();
    const { close } = useImportNodeModal();

    const [object, setObject] = useState<any>({});
    const queryClient = useQueryClient();

    useEffect(() => {
        const down = (e: KeyboardEvent) => {
            e.key === "Escape" && close();
        };

        document.addEventListener("keydown", down);
        return () => document.removeEventListener("keydown", down);
    });

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
                            importNode(diagram, object.id);
                            queryClient.refetchQueries({
                                queryKey: ["diagram"],
                            });
                            close();
                        }}
                    >
                        <div className={style.head}>
                            <span className="p-2 px-3">
                                Import Node from System
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
                                <ImportActivityNode
                                    object={object}
                                    setObject={setObject}
                                />
                            )}
                            {type == "classes" && (
                                <ImportClassNode
                                    object={object}
                                    setObject={setObject}
                                />
                            )}
                            {type == "usecase" && (
                                <ImportUsecaseNode
                                    object={object}
                                    setObject={setObject}
                                />
                            )}
                        </div>
                        <div className={style.actions}>
                            <Button
                                color="primary"
                                size="sm"
                                disabled={!object.id}
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

export default ImportNodeModal;
