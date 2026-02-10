import { useAuthEffect } from "$auth/hooks/authEffect";
import { useDiagram } from "$diagram/queries";
import { useDiagramStore } from "$diagram/stores";
import { authAxios } from "$lib/features/auth/state/auth";
import { queryClient } from "$shared/hooks/queryClient";
import { Chip } from "@mui/joy";
import { Save } from "lucide-react";
import React, { useState, useEffect } from "react";

const DiagramName: React.FC = () => {
    const { diagram, type} = useDiagramStore();
    const systemName = useDiagramStore((s) => s.systemName);
    const { data, isSuccess } = useDiagram(diagram);
    const defaultNames: { [type: string]: string } = {
        usecase: "Use Case Diagram",
        activity: "Activity Diagram",
        class: "Class Diagram",
    };

    const fallbackName = defaultNames[type] ?? "Class Diagram";
    const inputName = (data?.name ?? "").trim();
    const [name, setName] = useState("");

    useEffect(() => {
        if (!isSuccess) return;
        setName((data?.name ?? fallbackName).trim());
    }, [isSuccess, data?.name, fallbackName]);

    const deviationFlag = inputName !== (name ?? "").trim();

    const saveName = async () => {
        await authAxios.patch(`/v1/diagram/${diagram}/`, { name: name.trim() });
        queryClient.invalidateQueries({ queryKey: ["diagram", diagram] });
    };

    return isSuccess ? (
        <span className="mx-auto flex w-fit flex-row items-center gap-2">
            <span>
                <span className="text-stone-400">{systemName || "System"} /</span>
                <span
                    className="px-1"
                    contentEditable
                    suppressContentEditableWarning
                    onBlur={(e) => setName((e.currentTarget.textContent ?? "").trim())}
                >
                    {name}
                </span>
            </span>
            <Chip
                size="sm"
                onClick={deviationFlag ? saveName : undefined}
                color={deviationFlag ? "primary" : "neutral"}
            >
                <Save size={12} />
            </Chip>
        </span>
    ) : null;
};

export default DiagramName;
