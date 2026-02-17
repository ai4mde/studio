import { useDiagramStore } from "$diagram/stores";
import { partialUpdateNode } from "$diagram/mutations/diagram";
import { FormLabel, Input, Stack, Button } from "@mui/joy";
import React, { useState, useMemo } from "react";
import { Node } from "reactflow";

interface EditTextColorProps {
    node: Node;
}

export const EditTextColor: React.FC<EditTextColorProps> = ({ node }) => {
    const { diagram } = useDiagramStore();
    const [color, setColor] = useState(node.data?.text_color_hex || "#000000");
    
    const dirty = useMemo(
        () => color !== (node.data?.text_color_hex || "#000000"),
        [color, node.data?.text_color_hex],
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
                background_color_hex: node.data?.background_color_hex || "#ffffff",
                text_color_hex: color,
            },
        });
    };

    return (
        <Stack spacing={1}>
            <FormLabel>Text Color</FormLabel>
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
                    placeholder="#000000"
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

export default EditTextColor;
