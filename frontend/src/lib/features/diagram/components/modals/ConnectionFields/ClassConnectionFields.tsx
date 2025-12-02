import { FormControl, FormLabel, Input, Option, Select } from "@mui/joy";
import React from "react";

type Props = {
    object: any;
    setObject: (o: any) => void;
};

// Chaeck that string is not empty
const isNonEmpty = (v: unknown): boolean =>
    typeof v === "string" && v.trim().length > 0;

// Check property validity
export const isClassConnectionValid = (object: any): boolean => {
    const relType = object?.type;
    const mult = object?.multiplicity ?? {};

    if (relType === "association") {
        // label + both multiplicities required
        return (
            isNonEmpty(object?.label) &&
            isNonEmpty(mult.source) &&
            isNonEmpty(mult.target)
        );
    }

    if (relType === "composition") {
        // only multiplicities required
        return (
            isNonEmpty(mult.source) &&
            isNonEmpty(mult.target)
        );
    }

    // For other types (generalization, dependency)
    return !!relType;
};

export const ClassConnectionFields: React.FC<Props> = ({ object, setObject }) => {
    const relType = object?.type ?? null;
    const isAssociation = relType === "association";
    const isComposition = relType === "composition";
    const isDependency = relType === "dependency";
    const isAssocOrComp = isAssociation || isComposition;

    const  multiplicityOptions = [
        {value: "1", label: "1"},
        {value: "0..1", label: "0..1"},
        {value: "*", label: "*"},
        {value: "1..*", label: "1..*"},
    ] as const;

    const handleMultiplicityChange = (
        side: "source" | "target",
        value: string | null,
    ) => {
        const v = value ?? "";
        setObject((obj: any) => ({
            ...obj,
            multiplicity: {
                ...(obj.multiplicity ?? {}),
                [side]: v,
            },
        }));
    };

    return (
        <>
            {/* TYPE */}
            <FormControl size="sm" className="w-full">
                <FormLabel>Type</FormLabel>
                <Select
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
                    <FormControl required={isAssociation} size="sm" className="w-full">
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
                        <FormControl required size="sm" className="w-full">
                            <FormLabel>Source Multiplicity</FormLabel>
                            <Select
                                value={object?.multiplicity?.source ?? ""}
                                onChange={(_, value = "") => 
                                    handleMultiplicityChange("source", value)
                                }
                            >
                                {multiplicityOptions.map((opt) => (
                                    <Option
                                        key={opt.value}
                                        value={opt.value}
                                        label={opt.label}
                                    >
                                        {opt.label}
                                    </Option>
                                ))}
                            </Select>
                        </FormControl>

                        {/* TARGET MULTIPLICITY */}
                        <FormControl required size="sm" className="w-full">
                            <FormLabel>Target Multiplicity</FormLabel>
                            <Select
                                value={object?.multiplicity?.target ?? ""}
                                onChange={(_, value = "") => 
                                    handleMultiplicityChange("target", value)
                                }
                            >
                                {multiplicityOptions.map((opt) => (
                                    <Option
                                        key={opt.value}
                                        value={opt.value}
                                        label={opt.label}
                                    >
                                        {opt.label}
                                    </Option>
                                ))}
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

export default ClassConnectionFields;
