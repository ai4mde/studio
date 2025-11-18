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

export const EditConnectionModal: React.FC = () => {
    const modalState = useEditConnectionModal();
    const { diagram, edges, type } = useDiagramStore();

    const edge = useMemo(
        () => edges.find((e) => e.id == modalState.edge),
        [modalState.edge, edges],
    );

    console.log("EDGE DATA:", edge?.data);

    const [object, setObject] = useState<any>(edge?.data ?? {});

    useEffect(() => {
        setObject(edge?.data ?? {});
    }, [edge]);

    const connectionTypes = useMemo(() => {
        return schema.definitions.Edge.anyOf ?? [];
    }, []);

    const selectedType = useMemo(() => {
        return schema.definitions.Edge.anyOf.find(
            (e) => e.properties.type && e.properties.type.const == object.type,
        );
    }, [object, object.type, type]);

    const onDelete = () => {
        modalState?.edge && deleteEdge(diagram, modalState.edge);
    };

    useEffect(() => {
        const down = (e: KeyboardEvent) => {
            e.key === "Escape" && close();
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
                                    <FormControl size="sm">
                                        <FormLabel>Type</FormLabel>
                                        <Select
                                            placeholder="Select a connection type"
                                            value={object?.type ?? null}
                                            onChange={(_, value) => {
                                                setObject((obj: any) => ({
                                                    ...obj,
                                                    type: value,
                                                }));
                                            }}
                                        >
                                            {connectionTypes.map(
                                                (type, idx) =>
                                                    type.properties.type
                                                        ?.const && (
                                                        <Option
                                                            key={idx}
                                                            value={
                                                                type.properties
                                                                    .type.const
                                                            }
                                                        >
                                                            {
                                                                type.properties
                                                                    .type.const
                                                            }
                                                        </Option>
                                                    ),
                                            )}
                                        </Select>
                                    </FormControl>
                                    {selectedType &&
                                        Object.keys(
                                            selectedType.properties,
                                        ).includes("labels") && (
                                            <div className="flex w-full flex-row items-center justify-between gap-2">
                                                <FormControl size="sm">
                                                    <FormLabel>
                                                        Label From
                                                    </FormLabel>
                                                    <Input></Input>
                                                </FormControl>
                                                <FormControl size="sm">
                                                    <FormLabel>To</FormLabel>
                                                    <Input></Input>
                                                </FormControl>
                                            </div>
                                        )}
                                    {selectedType &&
                                        Object.keys(
                                            selectedType.properties,
                                        ).includes("multiplicity") && (
                                            <div className="flex w-full flex-row items-center justify-between gap-2">
                                                <FormControl size="sm">
                                                    <FormLabel>
                                                        Multiplicity From
                                                    </FormLabel>
                                                    <Input></Input>
                                                </FormControl>
                                                <FormControl size="sm">
                                                    <FormLabel>To</FormLabel>
                                                    <Input></Input>
                                                </FormControl>
                                            </div>
                                        )}
                                </div>
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

export default EditConnectionModal;
