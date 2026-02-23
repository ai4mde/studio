
import { Checkbox, FormControl, FormLabel, Input, Option, Select, Switch, FormHelperText, Button } from "@mui/joy";
import React, { useState, useEffect } from "react";

import { useDiagramStore } from "$diagram/stores";
import { RelatedNode } from "$diagram/types/diagramState"
import CodeEditorModal from "$lib/shared/components/Modals/CodeEditorModal";
import { useSystemObjectClassifiers, useSystemSignalClassifiers } from "../ImportNodeModal/queries/importNode";
import { useAuthEffect } from "$auth/hooks/authEffect";

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
            role: "swimlane",
            type: "swimlane",
            height: 1000,
            width: 300,
            horizontal: false,
        },
        action: {
            role: "action",
            type: "action",
            isAutomatic: false,
        },
        control: {
            role: "control",
            type: "decision",
            decisionInput: "",
            decisionInputFlow: "",
            page: "",
        },
        object: {
            role: "object",
            type: "object",
            name: "", // derived from selected class
        },
        event: {
            role: "event",
            type: "event",
            name: "", // derived from selected signal
        },
    };

    const isControl = object.role === "control";
    const isEvent = object.role === "event";

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

    const onChangeRole = (newRole: string | null) => {
        if (!newRole) return;

        setObject(() => {
            const next = { ...(DEFAULTS[newRole] ?? {}) };

            // Keep name only where chosen by user
            if (newRole !== "action") delete next.name;

            return next;
        });
    }

    useEffect(() => {
        if (!object.role) return;
        const d = DEFAULTS[object.role];
        if (!d) return;

        setObject((o: any) => {
            const next = { ...o };
            for (const k of Object.keys(d)) {
                if (next[k] === undefined) next[k] = d[k];
            }
            return next;
        });
    }, [object.role, setObject]);

    const objectClsNameById = React.useMemo(() => {
        const m = new Map<string, string>();
        for (const c of objectClassifiers ?? []) {
            if (c?.id && c?.data?.name) m.set(c.id, c.data.name);
        }
        return m;
    }, [objectClassifiers]);

    const signalNameById = React.useMemo(() => {
        const m = new Map<string, string>();
        for (const s of signalClassifiers ?? []) {
            if (s?.id && s?.data?.name) m.set(s.id, s.data.name);
        }
        return m;
    }, [signalClassifiers]);


    return (
        <>
            <FormControl size="sm" className="w-full">
                <FormLabel>Role</FormLabel>
                <Select
                    value={object.role || ""}
                    onChange={(_, r) => onChangeRole(r)}
                    placeholder="Select a role..."
                >
                    <Option value="swimlane">Swimlane</Option>
                    <Option value="action">Action</Option>
                    <Option value="control">Control</Option>
                    <Option value="object">Object</Option>
                    <Option value="event">Event</Option>
                </Select>
            </FormControl>

            {object.role === "control" && (
                <FormControl size="sm" className="w-full">
                    <FormLabel>Control Type</FormLabel>
                    <Select
                        value={object.type || "decision"}
                        onChange={(_, t) => {
                            if (!t) return;
                            setObject((o: any) => ({
                                ...o,
                                type: "decision",
                            }));
                        }}
                    >
                        <Option value="decision">Decision</Option>
                        <Option value="final">Final</Option>
                        <Option value="fork">Fork</Option>
                        <Option value="initial">Initial</Option>
                        <Option value="join">Join</Option>
                        <Option value="merge">Merge</Option>
                    </Select>
                </FormControl>
            )}
            {(object.role == "action") && (
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

            {object.role === "object" && (
                <>
                    <FormControl size="sm" className="w-full">
                        <FormLabel>Class</FormLabel>
                        <Select
                            placeholder={!objectClassifiersSuccess ? "Loading..." : "Choose a class..."}
                            value={object.cls ?? null}
                            onChange={(_, v) => {
                                const id = v ? String(v) : null;
                                const selected = objectClassifiers.find(c => c.id === id);
                                setObject(o => ({
                                    ...o,
                                    cls: id,
                                    name: selected?.data?.name ?? "",
                                }));
                            }}
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

            {object.role === "event" && (
                <>
                    <FormControl size="sm" className="w-full">
                        <FormLabel>Signal</FormLabel>
                        <Select
                            placeholder={!signalClassifiersSuccess ? "Loading..." : "Choose a signal..."}
                            value={object.signal ?? null}
                            onChange={(_, v) => {
                                const id = v ? String(v) : null;
                                const selected = signalClassifiers.find(c => c.id === id);
                                setObject(o => ({
                                    ...o,
                                    signal: id,
                                    name: selected?.data?.name ?? "",
                                }));
                            }}
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

            {(object.role == "swimlane") && (
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
