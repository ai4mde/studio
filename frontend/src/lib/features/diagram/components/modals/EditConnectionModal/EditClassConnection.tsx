import { FormControl, FormLabel, Input, Option, Select } from "@mui/joy";
import React from "react";

type Props = {
    object: any;
    setObject: (o: any) => void;
};

export const EditClassConnection: React.FC<Props> = ({ object, setObject }) => {
    const relType = object?.type ?? null;
    const isAssociation = relType === "association";
    const isComposition = relType === "composition";
    const isDependency = relType === "dependency";
    const isAssocOrComp = isAssociation || isComposition;

    return (
        <>
            {/* TYPE */}
            <FormControl size="sm" className="w-full">
                <FormLabel>Type</FormLabel>
                <Select
                    placeholder="Select a connection type"
                    value={relType}
                    onChange={(_, value) => {
                        setObject((obj: any) => ({
                            ...obj,
                            type: value,
                        }));
                    }}
                >
                    <Option value="association" label="Association">
                        Association
                    </Option>
                    <Option value="generalization" label="Generalization">
                        Generalization
                    </Option>
                    <Option value="composition" label="Composition">
                        Composition
                    </Option>
                    <Option value="dependency" label="Dependency">
                        Dependency
                    </Option>
                </Select>
            </FormControl>

            {/* ASSOCIATION / COMPOSITION FIELDS */}
            {isAssocOrComp && (
                <>
                    <FormControl size="sm" className="w-full">
                        <FormLabel>Label</FormLabel>
                        <Input
                            value={object?.label ?? ""}
                            onChange={(e) => {
                                const value = e.target.value;
                                setObject((obj: any) => ({
                                    ...obj,
                                    label: value,
                                }));
                            }}
                        />
                    </FormControl>

                    <div className="flex w-full flex-row items-center justify-between gap-2">
                        <FormControl size="sm" className="w-full">
                            <FormLabel>Source Label</FormLabel>
                            <Input
                                value={object?.labels?.source ?? ""}
                                onChange={(e) => {
                                    const value = e.target.value;
                                    setObject((obj: any) => ({
                                        ...obj,
                                        labels: {
                                            ...(obj.labels),
                                            source: value,
                                        },
                                    }));
                                }}
                            />
                        </FormControl>
                        <FormControl size="sm" className="w-full">
                            <FormLabel>Target Label</FormLabel>
                            <Input
                                value={object?.labels?.target ?? ""}
                                onChange={(e) => {
                                    const value = e.target.value;
                                    setObject((obj: any) => ({
                                        ...obj,
                                        labels: {
                                            ...(obj.labels),
                                            target: value,
                                        },
                                    }));
                                }}
                            />
                        </FormControl>
                    </div>

                    <div className="flex w-full flex-row items-center justify-between gap-2">
                        {/* SOURCE MULTIPLICITY */}
                        <FormControl size="sm" className="w-full">
                            <FormLabel>Source Multiplicity</FormLabel>
                            <Select
                                placeholder="Select source multiplicity"
                                value={object?.multiplicity?.source ?? ""}
                                onChange={(_, value = "") => {
                                    setObject((obj: any) => ({
                                        ...obj,
                                        multiplicity: {
                                            ...(obj.multiplicity),
                                            source: value,
                                        },
                                    }));
                                }}
                            >
                                <Option value="1" label="1">
                                    1
                                </Option>
                                <Option value="0..1" label="0..1">
                                    0..1
                                </Option>
                                <Option value="*" label="*">
                                    *
                                </Option>
                                <Option value="1..*" label="1..*">
                                    1..*
                                </Option>
                            </Select>
                        </FormControl>

                        {/* TARGET MULTIPLICITY */}
                        <FormControl size="sm" className="w-full">
                            <FormLabel>Target Multiplicity</FormLabel>
                            <Select
                                placeholder="Select target multiplicity"
                                value={object?.multiplicity?.target ?? ""}
                                onChange={(_, value = "") => {
                                    setObject((obj: any) => ({
                                        ...obj,
                                        multiplicity: {
                                            ...(obj.multiplicity),
                                            target: value,
                                        },
                                    }));
                                }}
                            >
                                <Option value="1" label="1">
                                    1
                                </Option>
                                <Option value="0..1" label="0..1">
                                    0..1
                                </Option>
                                <Option value="*" label="*">
                                    *
                                </Option>
                                <Option value="1..*" label="1..*">
                                    1..*
                                </Option>
                            </Select>
                        </FormControl>
                    </div>
                </>
            )}

            {/* DEPENDENCY */}
            {isDependency && (
                <FormControl size="sm" className="w-full">
                    <FormLabel>Label</FormLabel>
                    <Input
                        value={object?.label ?? ""}
                        onChange={(e) => {
                            const value = e.target.value;
                            setObject((obj: any) => ({
                                ...obj,
                                label: value,
                            }));
                        }}
                    />
                </FormControl>
            )}
        </>
    );
};

export default EditClassConnection;
