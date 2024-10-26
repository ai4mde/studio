import {
    Button,
    FormControl,
    FormLabel,
    Input,
    Option,
    Select,
} from "@mui/joy";
import { Plus, X } from "lucide-react";
import React, { useState } from "react";

type Props = {
    object: any;
    setObject: (o: any) => void;
};

export const NewClassNode: React.FC<Props> = ({ object, setObject }) => {
    const [literal, setLiteral] = useState("");

    return (
        <>
            <FormControl size="sm" className="w-full">
                <FormLabel>Type</FormLabel>
                <Select
                    value={object.type}
                    onChange={(_, e) =>
                        setObject((o: any) => ({ ...o, type: e }))
                    }
                    placeholder="Select a type..."
                >
                    <Option value="class">Class</Option>
                    <Option value="enum">Enum</Option>
                    <Option value="application">Application</Option>
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
            {object.type == "enum" && (
                <>
                    <FormControl size="sm" className="w-full gap-1">
                        <FormLabel>Literals</FormLabel>
                        {(object.literals ?? []).map((e: string, i: number) => (
                            <div key={e} className="flex flex-row gap-1">
                                <span className="w-full">{e}</span>
                                <Button
                                    size="sm"
                                    color="danger"
                                    onClick={() => {
                                        setObject((o: any) => {
                                            const literals = o.literals.slice();
                                            literals.splice(i, 1);

                                            return {
                                                ...o,
                                                literals: literals,
                                            };
                                        });
                                    }}
                                >
                                    <X />
                                </Button>
                            </div>
                        ))}
                        <div className="flex flex-row gap-1">
                            <Input
                                className="w-full"
                                placeholder="New Literal..."
                                value={literal}
                                onChange={(e) => setLiteral(e.target.value)}
                            />
                            <Button
                                size="sm"
                                onClick={() => {
                                    setObject((o: any) => ({
                                        ...o,
                                        literals: [
                                            ...(o.literals ?? []),
                                            literal,
                                        ],
                                    }));
                                    setLiteral("");
                                }}
                            >
                                <Plus />
                            </Button>
                        </div>
                    </FormControl>
                </>
            )}
        </>
    );
};
