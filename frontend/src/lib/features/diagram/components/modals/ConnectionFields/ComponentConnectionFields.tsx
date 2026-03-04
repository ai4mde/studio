import { Alert, FormControl, FormLabel, Option, Select } from "@mui/joy";
import React from "react"
import { RelatedNode } from "$diagram/types/diagramState";


type Props = {
    object: any
    interfaceNodes: RelatedNode[];
    setObject: (o: any) => void;
}

export const ComponentConnectionFields: React.FC<Props> = ({ object, interfaceNodes, setObject }) => {
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
                    <Option value='interface' label='interface'>
                        Interface
                    </Option>
                </Select>
            </FormControl>
            {object.type === 'interface' && (
                <>
                    <Alert color="warning" size="sm" className="my-2">
                        The source node of this edge will act as the <strong>provider</strong>.
                    </Alert>
                    <FormControl size="sm" className="w-full">
                        <FormLabel>Required</FormLabel>
                        <Select
                            value={object.required ?? null}
                            onChange={(_, v) =>
                                setObject((o: any) => ({
                                    ...o,
                                    required: v,
                                }))
                            }
                        >
                            {interfaceNodes
                                .filter(n => n.id !== object.provided)
                                .map(n => (
                                    <Option key={n.id} value={n.id}>
                                        {n.name}
                                    </Option>
                                ))
                            }
                        </Select>
                    </FormControl>
                    <FormControl size="sm" className="w-full">
                        <FormLabel>Provider</FormLabel>
                        <Select
                            value={object.provided ?? null}
                            onChange={(_, v) =>
                                setObject((o: any) => ({
                                    ...o,
                                    provided: v,
                                }))
                            }
                        >
                            {interfaceNodes
                                .filter(n => n.id !== object.required)
                                .map(n => (
                                    <Option key={n.id} value={n.id}>
                                        {n.name}
                                    </Option>
                                ))
                            }
                        </Select>
                    </FormControl>
                </> 
            )}
        </>
    );
};

export default ComponentConnectionFields