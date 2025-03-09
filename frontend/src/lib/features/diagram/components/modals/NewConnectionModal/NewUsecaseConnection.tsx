import { FormControl, FormLabel, Option, Select } from "@mui/joy";
import React from "react";

type Props = {
    object: any;
    setObject: (o: any) => void;
};

export const NewUsecaseConnection: React.FC<Props> = ({
    object,
    setObject,
}) => {
    // TODO: Use the sourceNode & targetNode to display names
    // or other identifying attribute
    //
    // const sourceNode = useMemo(
    //     () => nodes.find((e) => e.id === source),
    //     [nodes]
    // )
    //
    // const targetNode = useMemo(
    //     () => nodes.find((e) => e.id === target),
    //     [nodes]
    // )
    // interaction
    // extension
    // inclusion
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
                    <Option value="interaction" label="Interaction">
                        Interaction
                    </Option>
                    <Option value="extension" label="Extension">
                        Extension
                    </Option>
                    <Option value="inclusion" label="Inclusion">
                        Inclusion
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

export default NewUsecaseConnection;
