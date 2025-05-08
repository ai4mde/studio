import { FormControl, FormLabel, Input, Option, Select, Switch } from "@mui/joy";
import React, { useEffect } from "react";
import { Node } from "reactflow";
import { RelatedDiagram } from "$diagram/types/diagramState";

type Props = {
    object: any;
    sourceNode?: Node;
    classDiagrams?: RelatedDiagram[];
    setObject: (o: any) => void;
};

export const NewActivityConnection: React.FC<Props> = ({
    object,
    sourceNode,
    classDiagrams,
    setObject,
}) => {
    // Set some defaults on the edge
    useEffect(
        () => 
            setObject((o: any) => ({
                isDirected: o.isDirected ?? true,
                type: o.type ?? "controlflow",
                condition: sourceNode.type == "decision"
                    ? { isElse: true }
                    : o?.condition,
                ...o,
            })),
        [],
    );

    const operators = [
        { name: "==", label: "==", supportedTypes: ["int", "str", "bool"] },
        { name: "!=", label: "!=",  supportedTypes: ["int", "str", "bool"] },
        { name: "<", label: "<", supportedTypes: ["int"] },
        { name: "<=", label: "<=", supportedTypes: ["int"] },
        { name: ">", label: ">", supportedTypes: ["int"] },
        { name: ">=", label: ">=", supportedTypes: ["int"] },
    ]

    const aggregators = [
        { name: "sum", label: "SUM", supportedTypes: ["int"] },
        { name: "avg", label: "AVG", supportedTypes: ["int"] },
        { name: "min", label: "MIN", supportedTypes: ["int"] },
        { name: "max", label: "MAX", supportedTypes: ["int"] },
        { name: "count", label: "COUNT", supportedTypes: []},
    ]


    const getOverlappingSupportedTypes = () => {
        const operator = operators.find((op) => op.name === object.condition?.operator);
        const aggregator = aggregators.find((agg) => agg.name === object.condition?.aggregator);

        if (!operator && !aggregator) {
            return [];
        }
        if (!aggregator) {
            return operator.supportedTypes;
        }
        // Find the intersection of supported types
        return operator.supportedTypes.filter((type) => aggregator.supportedTypes.includes(type),);

    }

    // log object.condition?.target_attribute_type when it changes
    useEffect(() => {
        console.log(object.condition);
    }, [object.condition]);

    return (
        <>
            <FormControl size="sm" className="w-full">
                <FormLabel>Type</FormLabel>
                <Select
                    value={object.type || "controlflow"}
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
            </FormControl>
            <FormControl size="sm" className="w-full">
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

            {object.type == "controlflow" && sourceNode.type == "decision" && (
                <>
                    <FormControl size="sm" className="w-full">
                        <FormLabel>Else Condition</FormLabel>
                        <Switch
                            checked={object.condition?.isElse}
                            onChange={(e) =>
                                setObject((o: any) => ({
                                    ...o,
                                    condition: e.target.checked
                                        ? { 
                                            isElse: true,
                                            target_class: "",
                                            target_attribute: "",
                                            target_attribute_type: "",
                                            operator: "",
                                            aggregator: "",
                                            threshold: "",
                                        }
                                        : {
                                            ...o.condition,
                                            isElse: false,
                                        }
                                }))
                            }
                            sx={{ alignSelf: "flex-start" }}
                        />
                    </FormControl>
                    
                    {!object.condition?.isElse && (
                        <>
                            <FormControl size="sm" className="w-full">
                                <FormLabel>Class</FormLabel>
                                <Select
                                    value={object.condition?.target_class || ""}
                                    onChange={(_, v) =>
                                        setObject((o: any) => ({
                                            ...o,
                                            condition: {
                                                ...o.condition,
                                                target_class: v,
                                                target_attribute: "",
                                                target_attribute_type: "",
                                            },
                                        }))
                                    }
                                >
                                    {classDiagrams
                                        ?.flatMap((diagram) =>
                                            diagram.nodes.map((node) => ({
                                                id: node.id,
                                                name: node.name,
                                            }))
                                        )
                                        .map((node) => (
                                            <Option key={node.id} value={node.id}>
                                                {node.name}
                                            </Option>
                                        ))}
                                </Select>
                            </FormControl>
                            <FormControl size="sm" className="w-full">
                                <FormLabel>Aggregate function</FormLabel>
                                <Select
                                    value={object.condition?.aggregator || ""}
                                    onChange={(_, v) =>
                                        setObject((o: any) => ({
                                            ...o,
                                            condition: {
                                                ...o.condition,
                                                aggregator: v,
                                                target_attribute: "",
                                                target_attribute_type: "",
                                                threshold: "",
                                            },
                                        }))
                                    }
                                >
                                    <Option value="">None</Option>
                                    {aggregators
                                        .map((op) => (
                                            <Option key={op.name} value={op.name}>
                                                {op.label}
                                            </Option>
                                        ))}
                                </Select>
                            </FormControl>
                            <FormControl size="sm" className="w-full">
                                <FormLabel>Operator</FormLabel>
                                <Select
                                    value={object.condition?.operator || ""}
                                    onChange={(_, v) =>
                                        setObject((o: any) => ({
                                            ...o,
                                            condition: {
                                                ...o.condition,
                                                operator: v,
                                                target_attribute: "",
                                                target_attribute_type: "",
                                                threshold: "",
                                            },
                                        }))
                                    }
                                >
                                    {operators
                                        .map((op) => (
                                            <Option key={op.name} value={op.name}>
                                                {op.label}
                                            </Option>
                                        ))}
                                </Select>
                            </FormControl>
                            {object.condition?.operator && object.condition?.aggregator != 'count' && (
                                <FormControl size="sm" className="w-full">
                                    <FormLabel>Target Attribute</FormLabel>
                                    <Select
                                        value={object.condition?.target_attribute || ""}
                                        onChange={(_, v) => {
                                            const selectedAttribute = classDiagrams
                                                ?.flatMap((diagram) =>
                                                    diagram.nodes
                                                        .filter((node) => node.id === object.condition?.target_class)
                                                        .flatMap((node) => node.classAttributes)
                                                )
                                                .find((attr) => attr.name === v);
                                            
                                            setObject((o: any) => ({
                                                ...o,
                                                condition: {
                                                    ...o.condition,
                                                    target_attribute: selectedAttribute?.name || "",
                                                    target_attribute_type: selectedAttribute?.type || "",
                                                    threshold: "",
                                                },
                                            }));
                                        }}
                                    >
                                        {classDiagrams
                                            ?.flatMap((diagram) =>
                                                diagram.nodes
                                                    .filter((node) => node.id === object.condition?.target_class)
                                                    .flatMap((node) =>
                                                        node.classAttributes.filter(
                                                            (attr) =>
                                                                getOverlappingSupportedTypes().includes(attr.type)
                                                        )
                                                        .map((attr)=> ({
                                                            name: attr.name,
                                                            type: attr.type,
                                                        }))
                                                    )
                                            )
                                            .map((attr) => (
                                                <Option key={attr.name} value={attr.name}>
                                                    {attr.name} ({attr.type})
                                                </Option>
                                            ))}
                                    </Select>
                                </FormControl>
                            )}
                            {(object.condition?.target_attribute || (object.condition?.operator && object.condition?.aggregator === 'count')) && (
                                <FormControl size="sm" className="w-full">
                                <FormLabel>Condition value</FormLabel>
                                {(object.condition?.target_attribute_type === "int" || object.condition?.aggregator === "count") && (
                                <Input
                                        type="number"
                                        value={object.condition?.threshold || ""}
                                        onChange={(e) =>
                                            setObject((o: any) => ({
                                                ...o,
                                                condition: {
                                                    ...o.condition,
                                                    threshold: e.target.value,
                                                },
                                            }))
                                        }
                                    />
                                )}
                                {object.condition?.target_attribute_type === "str" && (
                                    <Input
                                        type="text"
                                        value={object.condition?.threshold || ""}
                                        onChange={(e) =>
                                            setObject((o: any) => ({
                                                ...o,
                                                condition: {
                                                    ...o.condition,
                                                    threshold: e.target.value,
                                                },
                                            }))
                                        }
                                    />
                                )}
                                {object.condition?.target_attribute_type === "bool" && (
                                    <Select
                                        value={object.condition?.threshold || ""}
                                        onChange={(_, v) =>
                                            setObject((o: any) => ({
                                                ...o,
                                                condition: {
                                                    ...o.condition,
                                                    threshold: v,
                                                },
                                            }))
                                        }
                                    >
                                        <Option value="true">True</Option>
                                        <Option value="false">False</Option>
                                    </Select>
                                )}
                                </FormControl>
                            )}
                        </>
                    )}
                </>
            )}
        </>
    );
};

export default NewActivityConnection;
