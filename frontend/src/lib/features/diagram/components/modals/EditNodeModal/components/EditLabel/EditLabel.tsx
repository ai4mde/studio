import { partialUpdateNode } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";
import { Button, FormLabel, Input, Stack } from "@mui/joy";
import React, { useMemo, useState } from "react";
import { Node } from "reactflow";

type Props = {
    node: Node;
};

const EditLabel: React.FC<Props> = ({ node }) => {
    const [label, setLabel] = useState(node?.data?.label ?? "");
    const { diagram } = useDiagramStore();
    
    const dirty = useMemo(
        () => label !== (node?.data?.label ?? ""),
        [label, node?.data?.label],
    );

    return (
        <Stack spacing={1}>
            <span className="w-full border-b border-solid border-gray-400 py-1 text-xs">
                Label
            </span>
            <Stack direction="row" spacing={1} alignItems="flex-end">
                <Input
                    type="text"
                    value={label}
                    onChange={(e) => setLabel(e.target.value)}
                    placeholder="Enter label"
                    slotProps={{
                        input: {
                            style: {
                                fontSize: "0.875rem",
                            },
                        },
                    }}
                />
                <Button
                    disabled={!dirty}
                    color="primary"
                    size="sm"
                    onClick={() =>
                        partialUpdateNode(diagram, node.id, {
                            cls: {
                                label: label,
                            },
                        })
                    }
                >
                    Save
                </Button>
            </Stack>
        </Stack>
    );
};

export default EditLabel;
