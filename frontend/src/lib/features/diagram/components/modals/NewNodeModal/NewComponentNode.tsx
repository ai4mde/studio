import { FormControl, FormLabel, Input, Option, Select } from "@mui/joy";
import React from "react";

type Props = {
    object: any;
    setObject: (o: any) => void;
}

export const NewComponentNode: React.FC<Props> = ({ object, setObject }) => {
    return (
        <>
            <FormControl size="sm" className="w-full">
                <FormLabel>Type</FormLabel>
                <Select
                    onChange={(_, v) =>
                        setObject((o: any) => ({
                            ...o,
                            type: v ?? null,
                        }))
                    }
                >
                    <Option value="system">System</Option>
                    <Option value="container">Container</Option>
                    <Option value="component">Component</Option>
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
                    placeholder={`Name of the ${object.type ?? "node"}...`}
                />
            </FormControl>
        </>
    );
};

