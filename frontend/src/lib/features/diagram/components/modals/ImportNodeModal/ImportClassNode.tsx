import { useDiagramStore } from "$diagram/stores";
import { FormControl, FormLabel, Option, Select } from "@mui/joy";
import React, { useState } from "react";
import { useSystemClassClassifiers } from "./queries/importNode";


type Props = {
    object: any;
    setObject: (o: any) => void;
};

export const ImportClassNode: React.FC<Props> = ({ object, setObject }) => {
    const system = useDiagramStore((s) => s.system);
    const [classifiers, isSuccess] = useSystemClassClassifiers(system);
    const [selectedClassifier, setSelectedClassifier] = useState(null);
    const normalize = (v: unknown) => (v ?? "").toString().toLowerCase();

    return (
        <>
            <FormControl size="sm" className="w-full">
                <FormLabel>Import a Class / Enum Node</FormLabel>
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
                        classifiers.map((e) => {
                            const sameSystem = normalize(e.system_id) === normalize(system);

                            return (
                                <Option value={e.id} sx={{"--Option-decoratorChildHeight": "0px",}}>{e.data.name} ({e.data.type}) 
                                    {!sameSystem && e.system_name && 
                                        <span className="ml-2 px-2 py-0.5 rounded-md text-xs fond-medium bg-gray-200 text-gray-700">
                                            {e.system_name}
                                        </span>
                                    }
                                </Option>
                            )
                        }
                        ))}
                </Select>
            </FormControl>
        </>
    );
};
