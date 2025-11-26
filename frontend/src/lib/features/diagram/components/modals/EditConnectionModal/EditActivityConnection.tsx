import { FormControl, FormLabel, Input, Option, Select } from "@mui/joy";
import React, { useEffect } from "react";

type Props = {
    object: any;
    setObject: (o: any) => void;
}

export const EditActivityConnection: React.FC<Props> = ({ object, setObject }) => {
    const relType = object?.type ?? "controlflow";
    const isObjectFlow = relType === "objectflow";

    const updateField =
        (field: "guard" | "weight" | "cls") =>
        (e: React.ChangeEvent<HTMLInputElement>) => {
            const value = e.target.value;
            setObject((o: any) => ({
                ...o,
                [field]: value,
            }));
        };

    return (
        <>
            {/* TYPE, GUARD, WEIGHT */}
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
                    <Option value="controlflow" label="ControlFlow">
                        ControlFlow
                    </Option>
                    <Option value="objectflow" label="ObjectFlow">
                        ObjectFlow
                    </Option>
                </Select>
            </FormControl>

            <FormControl size="sm" className="w-full">
                <FormLabel>Guard</FormLabel>
                <Input
                    value={object?.guard ?? ""}
                    onChange={updateField("guard")}
                />
            </FormControl>

            <FormControl size="sm" className="w-full">
                <FormLabel>Weight</FormLabel>
                <Input
                    value={object?.weight ?? ""}
                    onChange={updateField("weight")}
                />
            </FormControl>

            {/* CLASS */}
            {isObjectFlow && (
                <FormControl size="sm" className="w-full">
                    <FormLabel>Class</FormLabel>
                    <Input
                        value={object?.class ?? ""}
                        onChange={updateField("cls")}
                    />
                </FormControl>
            )}
        </>
    );
};

export default EditActivityConnection;
