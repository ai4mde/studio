import { useDiagramStore } from "$diagram/stores";
import { FormControl, FormLabel, Option, Select } from "@mui/joy";
import React, { useState } from "react";
import { useSystemActivityClassifiers } from "./queries/importNode";


type Props = {
    object: any;
    setObject: (o: any) => void;
};

export const ImportActivityNode: React.FC<Props> = ({ object, setObject }) => {
    const { system } = useDiagramStore();
    const [classifiers, isSuccess] = useSystemActivityClassifiers(system);
    const [selectedClassifier, setSelectedClassifier] = useState(null)

    return (
        <>
            <FormControl size="sm" className="w-full">
                <FormLabel>Import an Action Node</FormLabel>
                <Select
                    placeholder="Choose one…"
                    value={selectedClassifier}
                    onChange={(event, newValue) => {
                        setSelectedClassifier(newValue);
                        setObject((o: any) => ({ ...o, id: newValue }))
                    }}
                    required
                >
                    {isSuccess && (
                        classifiers.map((e) => (
                            <Option value={e.id}>{e.data.name} ({e.data.type})</Option>
                        )
                        ))}
                </Select>
            </FormControl>
        </>
    );
};
