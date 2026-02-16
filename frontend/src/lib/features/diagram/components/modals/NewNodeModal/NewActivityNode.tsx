
import { Checkbox, FormControl, FormLabel, Input, Option, Select, Switch, FormHelperText, Button } from "@mui/joy";
import React, { useEffect, useState } from "react";

import { useDiagramStore } from "$diagram/stores";
import { RelatedNode } from "$diagram/types/diagramState"
import CodeEditorModal from "$lib/shared/components/Modals/CodeEditorModal";
import { useSystemObjectClassifiers, useSystemSignalClassifiers } from "../ImportNodeModal/queries/importNode";

type Props = {
    object: any;
    uniqueActors: RelatedNode[];
    swimlaneGroupExists: boolean;
    existingActors: string[];
    classes?: string[];
    setObject: (o: any) => void;
};

export const NewActivityNode: React.FC<Props> = ({ object, uniqueActors, existingActors, swimlaneGroupExists, classes, setObject }) => {
    const systemId = useDiagramStore((s) => s.systemId);

    const [objectClassifiers, objectClassifiersSuccess] = useSystemObjectClassifiers(systemId);
    const [signalClassifiers, signalClassifiersSuccess] = useSystemSignalClassifiers(systemId);

    const DEFAULTS: Record<string, any> = {
        swimlane: {
            type: "swimlane",
            height: 1000,
            width: 300,
            horizontal: false,
        },
        action: {
            type: "action",
            isAutomatic: false,
        },
        control: {
            type: "control",
            subtype: "decision",
        },
        object: {
            type: "object",
        },
        event: {
            type: "event",
            subtype: "sent",
        },
    };

    const isControl = object.type === "control";
    const isEvent = object.type === "event";

    const [isCodeEditorOpen, setIsCodeEditorOpen] = useState(false);

    const handleOpenCodeEditor = () => setIsCodeEditorOpen(true);
    const handleCloseCodeEditor = () => setIsCodeEditorOpen(false);

    const handleSaveCode = (updateCode: string) => {
        setObject((o: any) => ({
            ...o,
            customCode: updateCode,
        }));
        handleCloseCodeEditor();
    }

    const onChangeType = (newType: string | null) => {
        setObject((o: any) => {
            const next: any = { ...(DEFAULTS[newType ?? ""] ?? {}) };
            next.name = "";
            return next;
        });
    };

    return (
        <>
            <FormControl size="sm" className="w-full">
                <FormLabel>Type</FormLabel>
                <Select
                    value={object.type || ""}
                    onChange={(_, v) => onChangeType(v)}
                    placeholder="Select a role..."
                >
                    <Option value="swimlane">Swimlane</Option>
                    <Option value="action">Action</Option>
                    <Option value="control">Control</Option>
                    <Option value="object">Object</Option>
                    <Option value="event">Event</Option>
                </Select>
            </FormControl>

            {(isControl || isEvent) && (
                <FormControl size="sm" className="w-full">
                    <FormLabel>Subtype</FormLabel>
                    <Select
                        value={object.subtype || ""}
                        placeholder="Select a subtype..."
                        onChange={(_, sub) => {
                            if (!sub) return;

                            if (isControl) {
                                setObject((o: any) => ({
                                    ...o,
                                    subtype: sub,
                                    variantType: sub,
                                }));
                            } else {
                                setObject((o: any) => ({ ...o, subtype: sub }));
                            }
                        }}
                    >
                        {isControl ? (
                            <>
                                <Option value="decision">Decision</Option>
                                <Option value="final">Final</Option>
                                <Option value="fork">Fork</Option>
                                <Option value="initial">Initial</Option>
                                <Option value="join">Join</Option>
                                <Option value="merge">Merge</Option>
                            </>
                        ) : (
                            <>
                                <Option value="sent">Sent</Option>
                                <Option value="received">Received</Option>
                            </>
                        )}
                    </Select>
                </FormControl>
            )}
            {(object.type == "action") && (
                <>
                    <FormControl size="sm" className="w-full">
                        <FormLabel>Name</FormLabel>
                        <Input
                            value={object.name || ""}
                            onChange={(e) =>
                                setObject((o: any) => ({
                                    ...o,
                                    name: e.target.value,
                                }))
                            }
                            placeholder={`Name of the ${object.type ?? "node"}...`}
                        />
                    </FormControl>
                    <FormControl size="sm" className="w-full">
                        <FormLabel>Execution Type</FormLabel>
                        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start" }}>
                            <div style={{ display: "flex", alignItems: "center" }}>
                                <Switch
                                    checked={object.isAutomatic || false}
                                    onChange={(e) =>
                                        setObject((o: any) => ({
                                            ...o,
                                            isAutomatic: e.target.checked,
                                        }))
                                    }
                                />
                            </div>
                            <FormHelperText>
                                {object.isAutomatic ? "Automatic" : "UI task"}
                            </FormHelperText>
                        </div>
                    </FormControl>
                    {object.isAutomatic && (
                        <Button
                            variant="outlined"
                            size="sm"
                            style={{ marginTop: "8px" }}
                            onClick={handleOpenCodeEditor}
                        >
                            Edit Code
                        </Button>
                    )}
                    <CodeEditorModal
                        open={isCodeEditorOpen}
                        onClose={handleCloseCodeEditor}
                        onSave={handleSaveCode}
                        initialCode={object.customCode}
                        classes={classes}
                    />
                </>
            )}

            {object.type === "object" && (
                <>
                    <FormControl size="sm" className="w-full">
                        <FormLabel>Name</FormLabel>
                        <Input
                            value={object.name || ""}
                            onChange={(e) => setObject((o: any) => ({ ...o, name: e.target.value }))}
                            placeholder="Name of the object..."
                        />
                    </FormControl>

                    <FormControl size="sm" className="w-full">
                        <FormLabel>Class (cls)</FormLabel>
                        <Select
                            placeholder={!objectClassifiersSuccess ? "Loading..." : "Choose a class..."}
                            value={object.cls ?? null}
                            onChange={(_, v) => setObject((o: any) => ({ ...o, cls: v }))}
                            disabled={!objectClassifiersSuccess}
                            required
                        >
                            {objectClassifiersSuccess &&
                                objectClassifiers.map((c) => (
                                    <Option key={c.id} value={c.id}>
                                        {c.data?.name} ({c.data?.type})
                                    </Option>
                                ))}
                        </Select>
                    </FormControl>

                    <FormControl size="sm" className="w-full">
                        <FormLabel>State (optional)</FormLabel>
                        <Input
                            value={object.state || ""}
                            onChange={(e) => setObject((o: any) => ({ ...o, state: e.target.value }))}
                            placeholder="e.g. pending, approved..."
                        />
                    </FormControl>
                </>
            )}

            {object.type === "event" && (
                <>
                    <FormControl size="sm" className="w-full">
                        <FormLabel>Name</FormLabel>
                        <Input
                            value={object.name || ""}
                            onChange={(e) => setObject((o: any) => ({ ...o, name: e.target.value }))}
                            placeholder="Name of the event..."
                        />
                    </FormControl>

                    <FormControl size="sm" className="w-full">
                        <FormLabel>Signal</FormLabel>
                        <Select
                            placeholder={!signalClassifiersSuccess ? "Loading..." : "Choose a signal..."}
                            value={object.signal ?? null}
                            onChange={(_, v) => setObject((o: any) => ({ ...o, signal: v }))}
                            disabled={!signalClassifiersSuccess}
                            required
                        >
                            {signalClassifiersSuccess &&
                                signalClassifiers.map((s) => (
                                    <Option key={s.id} value={s.id}>
                                        {s.data?.name} ({s.data?.type})
                                    </Option>
                                ))}
                        </Select>
                    </FormControl>
                </>
            )}

            {(object.type == "swimlane") && (
                <>
                    <FormControl size="sm" className="w-full">
                        <FormLabel>Actors</FormLabel>
                        <Select
                            multiple
                            placeholder="Select actors..."
                            onChange={(_, newValue) => {
                                const selectedNodes = uniqueActors.filter((node) => newValue.includes(node.id))
                                setObject((o: any) => ({
                                    ...o,
                                    swimlanes: selectedNodes.map((node) => ({
                                        role: "swimlane",
                                        type: "swimlane",
                                        actorNode: node.id,
                                        actorNodeName: node.name,
                                    }))
                                }))
                            }}
                        >
                            {uniqueActors
                                .filter((node) => !existingActors.includes(node.name))
                                .map((node) => (
                                    <Option key={node.id} value={node.id}>
                                        {node.name}
                                    </Option>
                                ))
                            }
                        </Select>
                    </FormControl>
                    {!swimlaneGroupExists && (
                        <>
                            <FormControl size="sm" className="w-full">
                                <FormLabel>Height</FormLabel>
                                <Input
                                    value={object.height || 1000}
                                    type="number"
                                    onChange={(e) =>
                                        setObject((o: any) => ({
                                            ...o,
                                            height: e.target.value,
                                        }))
                                    }
                                    placeholder="1000"
                                />
                            </FormControl>
                            <FormControl size="sm" className="w-full">
                                <FormLabel>Width</FormLabel>
                                <Input
                                    value={object.width || 300}
                                    type="number"
                                    onChange={(e) =>
                                        setObject((o: any) => ({
                                            ...o,
                                            width: e.target.value,
                                        }))
                                    }
                                    placeholder="300"
                                />
                            </FormControl>
                            <FormControl size="sm" className="w-full">
                                <FormLabel>Horizontal</FormLabel>
                                <Checkbox
                                    checked={object.horizontal || false}
                                    onChange={(e) =>
                                        setObject((o: any) => ({
                                            ...o,
                                            horizontal: e.target.checked,
                                        }))
                                    }
                                />
                            </FormControl>
                        </>
                    )}
                </>
            )}
        </>
    );
};
