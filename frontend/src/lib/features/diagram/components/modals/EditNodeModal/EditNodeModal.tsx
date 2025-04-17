import { deleteNode } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";
import { useEditNodeModal } from "$diagram/stores/modals";
import { authAxios } from "$lib/features/auth/state/auth";
import Editor from "@monaco-editor/react";
import Button from "@mui/joy/Button";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { X } from "lucide-react";
import React, { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import Draggable from "react-draggable";
import {
    EditApplication,
    EditAttributes,
    EditLiterals,
    EditMethods,
    EditName,
    EditBoolean,
    EditDimensions,
    EditSwimlane,
    EditCode,
} from "./components";
import style from "./editnodemodal.module.css";

export const EditNodeModal: React.FC = () => {
    const modalState = useEditNodeModal();
    const { diagram, nodes } = useDiagramStore();

    const node = useMemo(
        () => nodes.find((e) => e.id == modalState.node),
        [modalState.node, nodes],
    );

    const queryClient = useQueryClient();
    const nodeSchema = useQuery({
        queryKey: ["jsonschema", "node"],
        queryFn: async () => {
            const res = await authAxios.get(
                `/v1/diagram/specification/node.schema.json`,
            );
            return res.data;
        },
    });
    const updateNode = useMutation({
        mutationFn: async () => {
            await authAxios.patch(
                `/v1/diagram/${diagram}/node/${modalState.node}/`,
                {
                    cls: JSON.parse(raw).data,
                },
            );
            queryClient.invalidateQueries({
                queryKey: ["diagram"],
            });
        },
    });

    const [raw, setRaw] = useState(
        JSON.stringify({ data: node?.data ?? {} }, null, 2),
    );

    useEffect(() => {
        const down = (e: KeyboardEvent) => {
            e.key === "Escape" && close();
        };

        document.addEventListener("keydown", down);
        return () => document.removeEventListener("keydown", down);
    });

    const onDelete = () => {
        modalState?.node && deleteNode(diagram, modalState.node);
    };

    const nodeRef = React.useRef(null);

    return node ? (
        createPortal(
            <div className={style.modal}>
                <div className={style.wrapper}>
                    <Draggable
                        nodeRef={nodeRef}
                        key={`edit-${node.id}`}
                        handle=".handle"
                    >
                        <div ref={nodeRef} className={style.main}>
                            <div className={`${style.head} handle`}>
                                <span className="p-2 px-3">
                                    Edit Node ({node.id})
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
                                    {node.data?.name && (
                                        <EditName node={node} />
                                    )}
                                    {node.type == "class" && (
                                        <EditAttributes node={node} />
                                    )}
                                    {node.type == "class" && (
                                        <EditMethods node={node} />
                                    )}
                                    {node.type == "enum" && (
                                        <EditLiterals node={node} />
                                    )}
                                    {node.type == "application" && (
                                        <EditApplication node={node} />
                                    )}
                                    {node.type == 'swimlanegroup' && (
                                        <>
                                            <EditDimensions dimension='height' node={node} />
                                            <EditDimensions dimension='width' node={node} />
                                            <EditBoolean
                                                attribute="horizontal"
                                                node={node}
                                                helperText={{
                                                    trueText: "Horizontal",
                                                    falseText: "Vertical",
                                                }}
                                            />
                                            <EditSwimlane node={node} />
                                        </>
                                    )}
                                    {node.type == "action" && (
                                        <>
                                            <EditBoolean
                                                attribute="isAutomatic"
                                                node={node}
                                                helperText={{
                                                    trueText: "Automatic",
                                                    falseText: "Manual",
                                                }}
                                            />
                                            {node.data?.isAutomatic && (
                                                <EditCode
                                                    node={node}
                                                    attribute="customCode"
                                                />
                                            )}
                                        </>
                                    )}
                                </div>
                            </div>
                            <div className="bg-white p-3 text-xs">
                                <details>
                                    <summary className="select-none">
                                        &nbsp;Raw JSON Editor
                                    </summary>
                                    {nodeSchema.isSuccess && (
                                        <>
                                            <Editor
                                                key={
                                                    modalState.node ?? "default"
                                                }
                                                className="py-2"
                                                value={raw}
                                                language="json"
                                                options={{
                                                    lineNumbers: "off",
                                                    folding: false,
                                                }}
                                                beforeMount={(monaco) => {
                                                    monaco.languages.json.jsonDefaults.setDiagnosticsOptions(
                                                        {
                                                            validate: true,
                                                            schemas: [
                                                                {
                                                                    uri: "http://localhost:8000/api/model/specification/node/", // id of the first schema
                                                                    fileMatch: [
                                                                        "*",
                                                                    ], // associate with our model
                                                                    schema: nodeSchema.data,
                                                                },
                                                            ],
                                                        },
                                                    );
                                                }}
                                                height="16rem"
                                                width="100%"
                                                onChange={(e) =>
                                                    setRaw(e ?? "")
                                                }
                                            />
                                        </>
                                    )}
                                    <Button
                                        size="sm"
                                        className="w-full"
                                        onClick={() => {
                                            updateNode.mutate();
                                        }}
                                        disabled={
                                            !(
                                                raw !=
                                                JSON.stringify(
                                                    {
                                                        data: node?.data ?? {},
                                                    },
                                                    null,
                                                    2,
                                                )
                                            )
                                        }
                                    >
                                        Save
                                    </Button>
                                </details>
                            </div>
                            <div className={style.actions}>
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

export default EditNodeModal;
