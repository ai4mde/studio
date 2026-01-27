import { FormControl, FormLabel, Input, Option, Select } from "@mui/joy";
import React from "react";

type Props = {
    object: any;
    systemBoundaryExists: boolean;
    setObject: (o: any) => void;
};

export const NewUsecaseNode: React.FC<Props> = ({ object, systemBoundaryExists, setObject }) => {
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
                    <Option value="actor" label="Actor">
                        Actor
                    </Option>
                    <Option value="usecase" label="Use Case">
                        Use Case
                    </Option>
                    {!systemBoundaryExists && (
                        <Option value="system_boundary" label="System Boundary">
                            System Boundary
                        </Option>
                    )}
                </Select>
            </FormControl>
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
                />
            </FormControl>
        </>
    );
};
