import { FormControl, FormLabel, Input, Option, Select } from "@mui/joy";
import React, { useEffect } from "react";

type Props = {
    object: any;
    setObject: (o: any) => void;
};

export const NewActivityConnection: React.FC<Props> = ({
    object,
    setObject,
}) => {
    // Set some defaults on the edge
    useEffect(
        () =>
            setObject((o: any) => ({
                isDirected: true,
                type: "controlflow",
                ...o,
            })),
        [],
    );


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
                    <Option value="controlflow" label="ControlFlow">
                        ControlFlow
                    </Option>
                    <Option value="objectflow" label="ObjectFlow">
                        ObjectFlow
                    </Option>
                </Select>
                <FormLabel>Guard</FormLabel>
                <Input
                    value={object.guard}
                    onChange={(e) =>
                        setObject((o: any) => ({
                            ...o,
                            guard: e.target.value,
                        }))
                    }
                ></Input>
            </FormControl>
            <FormControl size="sm" className="w-full">
                <FormLabel>Weight</FormLabel>
                <Input
                    value={object.weight}
                    onChange={(e) =>
                        setObject((o: any) => ({
                            ...o,
                            weight: e.target.value,
                        }))
                    }
                ></Input>
            </FormControl>

            {object.type == "objectflow" && (
                <>
                    <FormControl size="sm" className="w-full">
                        <FormLabel>Class</FormLabel>
                        <Input
                            value={object.cls}
                            onChange={(e) =>
                                setObject((o: any) => ({
                                    ...o,
                                    cls: e.target.value,
                                }))
                            }
                        ></Input>
                    </FormControl>
                </>
            )}
        </>
    );
};

export default NewActivityConnection;
