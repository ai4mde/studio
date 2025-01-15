import { FormControl, FormLabel, Input, Option, Select } from "@mui/joy";
import React from "react";

type Props = {
    object: any;
    setObject: (o: any) => void;
};

export const NewActivityConnection: React.FC<Props> = ({
    object,
    setObject,
}) => {
    return (
        <>
            <FormControl size="sm" className="w-full">
                <FormLabel>Type</FormLabel>
                <Select
                    value={object.type}
                    onChange={(_, v) =>
                        setObject((o: any) => ({
                            ...o,
                            type: v,
                        }))
                    }
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

            {object.type == "association" && (
                <>
                    <FormControl required size="sm" className="w-full">
                        <FormLabel>Label</FormLabel>
                        <Input
                            value={object.label}
                            onChange={(e) =>
                                setObject((o: any) => ({
                                    ...o,
                                    label: e.target.value,
                                }))
                            }
                        />
                    </FormControl>
                    <div className="flex w-full flex-row gap-2">
                        <FormControl size="sm" className="w-full">
                            <FormLabel>Source Label</FormLabel>
                            <Input
                                value={object.labels?.source}
                                onChange={(e) =>
                                    setObject((o: any) => ({
                                        ...o,
                                        labels: {
                                            ...o.labels,
                                            source: e.target.value,
                                        },
                                    }))
                                }
                            />
                        </FormControl>
                        <FormControl size="sm" className="w-full">
                            <FormLabel>Target Label</FormLabel>
                            <Input
                                value={object.labels?.target}
                                onChange={(e) =>
                                    setObject((o: any) => ({
                                        ...o,
                                        labels: {
                                            ...o.labels,
                                            target: e.target.value,
                                        },
                                    }))
                                }
                            />
                        </FormControl>
                    </div>
                    <div className="flex w-full flex-row gap-2">
                        <FormControl required size="sm" className="w-full">
                            <FormLabel>Source Multiplicity</FormLabel>
                            <Select
                                required
                                value={object.multiplicity?.source?.lower}
                                onChange={(_, v) =>
                                    setObject((o: any) => ({
                                        ...o,
                                        multiplicity: {
                                            ...o.multiplicity,
                                            source: v,
                                        },
                                    }))
                                }
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
                        <FormControl required size="sm" className="w-full">
                            <FormLabel>Target Multiplicity</FormLabel>
                            <Select
                                required
                                value={object.multiplicity?.target?.lower}
                                onChange={(_, v) =>
                                    setObject((o: any) => ({
                                        ...o,
                                        multiplicity: {
                                            ...o.multiplicity,
                                            target: v,
                                        },
                                    }))
                                }
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

            {object.type == "generalization" && <></>}

            {object.type == "composition" && (
                <>
                    <FormControl size="sm" className="w-full">
                        <FormLabel>Label</FormLabel>
                        <Input
                            value={object.label}
                            onChange={(e) =>
                                setObject((o: any) => ({
                                    ...o,
                                    label: e.target.value,
                                }))
                            }
                        />
                    </FormControl>
                    <div className="flex w-full flex-row gap-2">
                        <FormControl size="sm" className="w-full">
                            <FormLabel>Source Label</FormLabel>
                            <Input
                                value={object.labels?.source}
                                onChange={(e) =>
                                    setObject((o: any) => ({
                                        ...o,
                                        multiplicity: {
                                            ...o.multiplicity,
                                            source: e.target.value,
                                        },
                                    }))
                                }
                            />
                        </FormControl>
                        <FormControl size="sm" className="w-full">
                            <FormLabel>Target Label</FormLabel>
                            <Input
                                value={object.labels?.target}
                                onChange={(e) =>
                                    setObject((o: any) => ({
                                        ...o,
                                        multiplicity: {
                                            ...o.multiplicity,
                                            target: e.target.value,
                                        },
                                    }))
                                }
                            />
                        </FormControl>
                    </div>
                    <div className="flex w-full flex-row gap-2">
                        <FormControl required size="sm" className="w-full">
                            <FormLabel>Source Multiplicity</FormLabel>
                            <Select
                                required
                                value={object.multiplicity?.source?.lower}
                                onChange={(_, v) =>
                                    setObject((o: any) => ({
                                        ...o,
                                        multiplicity: {
                                            ...o.multiplicity,
                                            source: v,
                                        },
                                    }))
                                }
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
                        <FormControl required size="sm" className="w-full">
                            <FormLabel>Target Multiplicity</FormLabel>
                            <Select
                                required
                                value={object.multiplicity?.target?.lower}
                                onChange={(_, v) =>
                                    setObject((o: any) => ({
                                        ...o,
                                        multiplicity: {
                                            ...o.multiplicity,
                                            target: v,
                                        },
                                    }))
                                }
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

            {object.type == "dependency" && (
                <>
                    <FormControl size="sm" className="w-full">
                        <FormLabel>Label</FormLabel>
                        <Input
                            value={object.label}
                            onChange={(e) =>
                                setObject((o: any) => ({
                                    ...o,
                                    label: e.target.value,
                                }))
                            }
                        />
                    </FormControl>
                </>
            )}
        </>
    );
};

export default NewActivityConnection;
