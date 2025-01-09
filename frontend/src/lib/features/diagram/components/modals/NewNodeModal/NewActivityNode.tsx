import { FormControl, FormLabel, Input, Option, Select } from "@mui/joy";
import React from "react";

type Props = {
    object: any;
    setObject: (o: any) => void;
};

export const NewActivityNode: React.FC<Props> = ({ object, setObject }) => {
    return (
        <>
            <FormControl size="sm" className="w-full">
                <FormLabel>Role</FormLabel>
                <Select
                    value={object.role}
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
                    value={object.type}
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
            {(object.type == "action" || object.type == "swimlane") && (
                <FormControl size="sm" className="w-full">
                    <FormLabel>Name</FormLabel>
                    <Input
                        value={object.name}
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
                        <FormLabel>Width</FormLabel>
                        <Input
                            value={object.width}
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
                            value={object.height}
                            type="number"
                            onChange={(e) =>
                                setObject((o: any) => ({
                                    ...o,
                                    height: e.target.value,
                                }))
                            }
                        />
                    </FormControl>
                </>
            )}
        </>
    );
};
