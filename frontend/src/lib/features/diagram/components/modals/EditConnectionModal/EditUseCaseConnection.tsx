import { FormControl, FormLabel, Input, Option, Select } from "@mui/joy";
import React, { useEffect } from "react";

type Props = {
    object: any;
    setObject: (o: any) => void;
}

export const EditUseCaseConnection: React.FC<Props> = ({ object, setObject }) => {
    const relType = object?.type ?? "controlflow";

    return (
        <>
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
                    <Option value="interaction" label="Interaction">
                        Interaction
                    </Option>
                    <Option value="extension" label="Extension">
                        Extension
                    </Option>
                    <Option value="inclusion" label="Inclusion">
                        Inclusion
                    </Option>
                    <Option value="generalization" label="Generalization">
                        Generalization
                    </Option>
                </Select>
            </FormControl>

        </>
    );
};

export default EditUseCaseConnection;
