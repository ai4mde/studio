import { useDiagramStore } from "$diagram/stores";
import { Lock, Tag, Unlock } from "lucide-react";
import React, { useState } from "react";

export const DiagramLock: React.FC = () => {
    const [locked] = useState(false);

    const { lock, requestLock, releaseLock } = useDiagramStore();

    return (
        <li className="h-full flex items-center">
            {locked ? (
                <Tag className="h-fit" type="red">
                    <span className="flex flex-row gap-1 items-center">
                        <Lock size={10} />
                        Diagram Locked (Read)
                    </span>
                </Tag>
            ) : lock ? (
                <Tag
                    className="h-fit"
                    type="blue"
                    onClick={() => releaseLock()}
                >
                    <span className="flex flex-row gap-1 items-center">
                        <Lock size={10} />
                        Diagram Locked (Edit)
                    </span>
                </Tag>
            ) : (
                <Tag
                    className="h-fit"
                    type="gray"
                    onClick={() => requestLock()}
                >
                    <span className="flex flex-row gap-1 items-center">
                        <Unlock size={10} />
                        Lock to Edit
                    </span>
                </Tag>
            )}
        </li>
    );
};

export default DiagramLock;
