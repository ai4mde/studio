import { useDiagramStore } from "$diagram/stores";
import { Lock, Unlock } from "lucide-react";
import { Chip } from "@mui/joy";
import React, { useState } from "react";

export const DiagramLock: React.FC = () => {
    const [locked] = useState(false);

    const { lock, requestLock, releaseLock } = useDiagramStore();

    return (
        <li className="flex h-full items-center">
            {locked ? (
                <Chip size="sm" color="danger" variant="outlined">
                    <span className="flex flex-row items-center gap-1">
                        <Lock size={10} />
                        Diagram Locked (Read)
                    </span>
                </Chip>
            ) : lock ? (
                <Chip
                    size="sm"
                    color="primary"
                    variant="outlined"
                    onClick={() => releaseLock()}
                >
                    <span className="flex flex-row items-center gap-1">
                        <Lock size={10} />
                        Diagram Locked (Edit)
                    </span>
                </Chip>
            ) : (
                <Chip
                    size="sm"
                    color="neutral"
                    variant="outlined"
                    onClick={() => requestLock()}
                >
                    <span className="flex flex-row items-center gap-1">
                        <Unlock size={10} />
                        Lock to Edit
                    </span>
                </Chip>
            )}
        </li>
    );
};

export default DiagramLock;
