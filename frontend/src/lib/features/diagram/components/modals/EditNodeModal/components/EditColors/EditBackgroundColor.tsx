import { useDiagramStore } from "$diagram/stores";
import { partialUpdateNode } from "$diagram/mutations/diagram";
import { FormLabel, Input, Stack, Button } from "@mui/joy";
import React, { useState, useMemo } from "react";
import { Node } from "reactflow";

interface EditBackgroundColorProps {
    node: Node;
}

export const EditBackgroundColor: React.FC<EditBackgroundColorProps> = ({ node }) => {
    const { diagram, projectSettings } = useDiagramStore();
    
    const getEffectiveColor = () => {
        if (node.data?.background_color_hex_override) {
            return node.data.background_color_hex_override;
        }
        if (projectSettings?.classifier_colors?.[node.data?.type]) {
            return projectSettings.classifier_colors[node.data.type].background_hex;
        }
        return "#FFFFFF";
    };
    
    const [color, setColor] = useState(getEffectiveColor());
    
    const dirty = useMemo(
        () => color !== getEffectiveColor(),
        [color, node.data?.background_color_hex_override, projectSettings],
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
                background_color_hex_override: color || undefined,
                text_color_hex_override: node.data?.text_color_hex_override,
            },
        });
    };

    const handleRestore = () => {
        partialUpdateNode(diagram, node.id, {
            data: {
                position: node.position || { x: 0, y: 0 },
                background_color_hex_override: undefined,
                text_color_hex_override: node.data?.text_color_hex_override,
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
                <Button
                    disabled={!node.data?.background_color_hex_override}
                    color="neutral"
                    variant="outlined"
                    size="sm"
                    onClick={handleRestore}
                >
                    Set Default
                </Button>
            </Stack>
        </Stack>
    );
};

export default EditBackgroundColor;
