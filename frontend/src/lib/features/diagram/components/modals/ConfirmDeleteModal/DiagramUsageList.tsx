import React from "react";
import { DiagramUsageItem } from "$diagram/types/diagramUsage";

type Props = {
    usages: DiagramUsageItem[];
};

export const DiagramUsageList: React.FC<Props> = ({ usages }) => {
    if (!usages?.length) return null;

    return (
        <ul className="list-disc pl-6 mt-2 space-y-1">
            {usages.map((u) => (
                <li key={`${u.diagram_id}-${u.system_id}`}>
                    Diagram {u.diagram_name} in system {u.system_name}.
                </li>
            ))}
        </ul>
    );
};
