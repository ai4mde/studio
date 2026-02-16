import { Button, Input, Stack } from "@mui/joy";
import { Trash2 } from "lucide-react";
import React, { useState } from "react";
import { Node } from "reactflow";

type Props = {
    technology: string;
    update: (v: string) => void;
    del: () => void;
    node: Node;
};

export const EditTechnology: React.FC<Props> = ({ technology, update, del }) => {
    const [value, setValue] = useState(technology);

    return (
        <Stack direction="row" spacing={1} alignItems="flex-end">
            <Input
                type="text"
                value={value}
                onChange={(e) => {
                    setValue(e.target.value);
                    update(e.target.value);
                }}
                placeholder="e.g., Python, React, Docker"
                slotProps={{
                    input: {
                        style: {
                            fontSize: "0.875rem",
                        },
                    },
                }}
            />
            <Button
                color="danger"
                variant="outlined"
                size="sm"
                onClick={del}
                sx={{ minWidth: "32px", padding: 1 }}
            >
                <Trash2 size={16} />
            </Button>
        </Stack>
    );
};

export default EditTechnology;
