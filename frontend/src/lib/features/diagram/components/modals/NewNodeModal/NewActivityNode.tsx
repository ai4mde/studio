import { FormControl, FormLabel, Input, Option, Select, Checkbox } from "@mui/joy";
import React, { useEffect } from "react";
import { RelatedDiagram, RelatedNode } from "$diagram/types/diagramState";

type Props = {
    object: any;
    relatedDiagrams: RelatedDiagram[];
    setObject: (o: any) => void;
};

export const NewActivityNode: React.FC<Props> = ({ object, relatedDiagrams, setObject }) => {
    // If the object is a swimlane, the default value for vertical is true
    useEffect(() => {
        if (object.vertical === undefined) {
            setObject((o: any) => ({
                ...o,
                vertical: true,
            }));
        }
    }, [object, setObject]);

    const uniqueActors = Array.from(
        relatedDiagrams.flatMap((diagram) => diagram.nodes).reduce((map, node) => {
            if (!map.has(node.name)) {
                map.set(node.name, node);
            }
            return map;
        }, new Map<string, RelatedNode>()).values()
    );

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
            )}
            {object.type == "swimlane" && (
                <>
                    <FormControl size="sm" className="w-full">
                        <FormLabel>Actor</FormLabel>
                        <Select
                            value={object.actorNode || ""}
                            onChange={(e, newValue) =>
                                setObject((o: any) => ({
                                    ...o,
                                    actorNode: newValue,
                                }))
                            }
                            placeholder="Select an actor..."
                        >
                            {uniqueActors.map((node) => (
                                <Option key={node.id} value={node.id}>
                                    {node.name}
                                </Option>
                            ))}
                        </Select>
                    </FormControl>
                    <FormControl size="sm" className="w-full">
                        <FormLabel>Width</FormLabel>
                        <Input
                            value={object.width || ""}
                            type="number"
                            onChange={(e) =>
                                setObject((o: any) => ({
                                    ...o,
                                    width: e.target.value,
                                }))
                            }
                        />
                    </FormControl>
                    <FormControl size="sm" className="w-full">
                        <FormLabel>Height</FormLabel>
                        <Input
                            value={object.height || ""}
                            type="number"
                            onChange={(e) =>
                                setObject((o: any) => ({
                                    ...o,
                                    height: e.target.value,
                                }))
                            }
                        />
                    </FormControl>
                    <FormControl size="sm" className="w-full">
                        <FormLabel>Vertical</FormLabel>
                        <Checkbox
                           checked={object.vertical || false}
                           onChange={(e) => 
                                 setObject((o: any) => ({
                                      ...o,
                                      vertical: e.target.checked,
                                 }))
                           }
                        />
                    </FormControl>
                </>
            )}
        </>
    );
};
