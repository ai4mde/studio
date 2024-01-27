import { useDiagram } from "$diagram/queries";
import { useDiagramStore } from "$diagram/stores";
import { authAxios } from "$lib/features/auth/state/auth";
import { queryClient } from "$shared/hooks/queryClient";
import { Chip } from "@mui/joy";
import { Save } from "lucide-react";
import React, { useState } from "react";

const DiagramName: React.FC = () => {
    const { diagram, type } = useDiagramStore();
    const { data, isSuccess } = useDiagram(diagram);
    const defaultNames: { [type: string]: string } = {
        usecase: "Use Case Diagram",
        activity: "Activity Diagram",
        class: "Class Diagram",
    };

    const [name, setName] = useState(
        data.name ?? defaultNames[type] ?? "Class Diagram"
    );

    const saveName = () => {
        authAxios
            .patch(`/api/model/diagram/${diagram}/`, {
                name: name,
            })
            .then(() =>
                queryClient.invalidateQueries({
                    queryKey: ["diagram", diagram],
                })
            );
    };

    return isSuccess ? (
        <span className="flex flex-row items-center w-fit gap-2 mx-auto">
            <span>
                <span className="text-stone-400">System /</span>
                <span
                    className="px-1"
                    contentEditable
                    suppressContentEditableWarning
                    onBlur={(e) => setName(e.currentTarget.textContent)}
                >
                    {name}
                </span>
            </span>
            <Chip
                size="sm"
                onClick={data.name != name ? saveName : undefined}
                color={data.name != name ? "primary" : "neutral"}
            >
                <Save size={12} />
            </Chip>
        </span>
    ) : (
        <></>
    );
};

export default DiagramName;
