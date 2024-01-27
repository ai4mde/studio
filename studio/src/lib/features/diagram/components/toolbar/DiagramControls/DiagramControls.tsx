import { DiagramLock } from "$diagram/components/toolbar/DiagramLock/DiagramLock";
import { useDiagram } from "$diagram/queries";
import { useDiagramStore } from "$diagram/stores";
import { ArrowLeft } from "lucide-react";
import React from "react";
import DiagramName from "../DiagramName/DiagramName";

const DiagramControls: React.FC = () => {
    const { diagram } = useDiagramStore();
    const { data } = useDiagram(diagram);

    return (
        <div className="w-full h-full items-center text-sm flex flex-row gap-2 px-2">
            <li className="h-full flex items-center">
                <a href={`/projects/${data?.project}/systems/${data?.system}`}>
                    <ArrowLeft size={14} />
                </a>
            </li>
            <DiagramLock />
            <DiagramName />
        </div>
    );
};

export default DiagramControls;
