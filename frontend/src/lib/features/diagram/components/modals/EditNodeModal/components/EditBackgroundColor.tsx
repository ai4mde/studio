import { useDiagramStore } from "$diagram/stores";
import { partialUpdateNode } from "$diagram/mutations/diagram";
import { FormLabel, Input, Stack, Button } from "@mui/joy";
import React, { useState, useMemo } from "react";
import { Node } from "reactflow";

interface EditBackgroundColorProps {
    node: Node;
}

export const EditBackgroundColor: React.FC<EditBackgroundColorProps> = ({ node }) => {
    const { diagram } = useDiagramStore();
    const [color, setColor] = useState(node.data?.background_color_hex || "#FFFFFF");
    
    const dirty = useMemo(
        () => color !== (node.data?.background_color_hex || "#FFFFFF"),
        [color, node.data?.background_color_hex],
    );

    const handleColorChange = (newColor: string) => {
        setColor(newColor);
    };

    const handleHexInput = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setColor(value);
    };

    const handleSave = () => {
        partialUpdateNode(diagram, node.id, {
            data: {
                position: node.position || { x: 0, y: 0 },
                background_color_hex: color,
            },
        });
    };

    return (
        <Stack spacing={1}>
            <FormLabel>Background Color</FormLabel>
            <Stack direction="row" spacing={1} alignItems="center">
                <Input
                    type="color"
                    value={color}
                    onChange={(e) => handleColorChange(e.target.value)}
                    slotProps={{
                        input: {
                            style: {
                                cursor: "pointer",
                                padding: "4px",
                                height: "40px",
                                width: "80px",
                            },
                        },
                    }}
                />
                <Input
                    type="text"
                    value={color}
                    onChange={handleHexInput}
                    placeholder="#FFFFFF"
                    slotProps={{
                        input: {
                            style: {
                                fontFamily: "monospace",
                                fontSize: "0.875rem",
                            },
                        },
                    }}
                />
                <Button
                    disabled={!dirty}
                    color="primary"
                    size="sm"
                    onClick={handleSave}
                >
                    Save
                </Button>
            </Stack>
        </Stack>
    );
};

export default EditBackgroundColor;
