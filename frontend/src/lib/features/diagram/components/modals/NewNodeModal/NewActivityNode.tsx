import { Checkbox, FormControl, FormLabel, Input, Option, Select, Switch, FormHelperText, Button } from "@mui/joy";
import React, { useEffect, useState } from "react";
import { RelatedNode } from "$diagram/types/diagramState"
import CodeEditorModal from "$lib/shared/components/Modals/CodeEditorModal";

type Props = {
    object: any;
    uniqueActors: RelatedNode[];
    swimlaneGroupExists: boolean;
    existingActors: string[];
    classes?: string[];
    setObject: (o: any) => void;
};

export const NewActivityNode: React.FC<Props> = ({ object, uniqueActors, existingActors,  swimlaneGroupExists, classes, setObject }) => {

    // Set default values for swimlane
    useEffect(() => {
        if (object.role === "swimlane") {
            setObject((o: any) => ({
                ...o,
                height: o.height || 1000,
                width: o.width || 300,
                horizontal: o.horizontal || false,
            }))
        }
    }, [object.role, setObject])

    // Set default values for action
    useEffect(() => {
        if (object.type === "action" && object.isAutomatic === undefined) {
            setObject((o: any) => ({
                ...o,
                isAutomatic: false,
            }));
        }
    }, [object.type, setObject]);


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

    return (
        <>
            <FormControl size="sm" className="w-full">
                <FormLabel>Role</FormLabel>
                <Select
                    value={object.role || ""}
                    onChange={(_, e) =>
                        setObject((o: any) => ({ ...o, role: e }))
                    }
                    placeholder="Select a role..."
                >
                    <Option value="swimlane">Swimlane</Option>
                    <Option value="action">Action</Option>
                    <Option value="control">Control</Option>
                    <Option value="object">Object</Option>
                </Select>
            </FormControl>
            <FormControl size="sm" className="w-full">
                <FormLabel>Type</FormLabel>
                <Select
                    value={object.type || ""}
                    placeholder="Select a type..."
                    onChange={(_, e) =>
                        setObject((o: any) => ({ ...o, type: e }))
                    }
                >
                    {object.role == "swimlane" && (
                        <>
                            <Option value="swimlane">Swimlane</Option>
                        </>
                    )}
                    {object.role == "action" && (
                        <>
                            <Option value="action">Action</Option>
                        </>
                    )}
                    {object.role == "control" && (
                        <>
                            <Option value="decision">Decision</Option>
                            <Option value="final">Final</Option>
                            <Option value="fork">Fork</Option>
                            <Option value="initial">Initial</Option>
                            <Option value="join">Join</Option>
                            <Option value="merge">Merge</Option>
                        </>
                    )}
                    {object.role == "object" && (
                        <>
                            <Option value="class" disabled>Class</Option>
                            <Option value="buffer" disabled>Buffer</Option>
                            <Option value="pin" disabled>Pin</Option>
                        </>
                    )}
                </Select>
            </FormControl>
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
            {(object.type == "swimlane") && (
                <>
                    <FormControl size="sm" className="w-full">
                        <FormLabel>Actors</FormLabel>
                        <Select
                            multiple
                            placeholder="Select actors..."
                            onChange={(_, newValue) =>{
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
