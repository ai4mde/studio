import { FormControl, FormLabel, Input, Option, Select } from "@mui/joy";
import React from "react";
import { RelatedNode } from "$diagram/types/diagramState"


type Props = {
    object: any;
    systemBoundaryExists: boolean;
    systemNodes: RelatedNode[];
    setObject: (o: any) => void;
};

export const NewUsecaseNode: React.FC<Props> = ({ object, systemBoundaryExists, systemNodes, setObject }) => {
    return (
        <>
            <FormControl size="sm" className="w-full">
                <FormLabel>Type</FormLabel>
                <Select
                    value={object.type ?? null}
                    onChange={(_, v) =>
                        setObject((o: any) => ({
                            ...o,
                            type: v ?? null,
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
                    value={object.name ?? ""}
                    onChange={(e) =>
                        setObject((o: any) => ({
                            ...o,
                            name: e.target.value,
                        }))
                    }
                />
            </FormControl>
            {object.type === "system_boundary" && (
              <FormControl size="sm" className="w-full">
                <FormLabel>System</FormLabel>
                <Select
                  placeholder="Select optional system node..."
                  value={object.system_id ?? null}
                  onChange={(_, newValue) => {
                    setObject((o: any) => ({
                      ...o,
                      system_id: newValue,
                    }));
                  }}
                >
                  {systemNodes.map((node) => (
                    <Option key={node.cls} value={node.cls}>
                      {node.name}
                    </Option>
                  ))}
                </Select>
              </FormControl>
            )}
        </>
    );
};
