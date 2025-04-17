import { partialUpdateNode } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";
import { Save } from "lucide-react";
import React, { useState } from "react";
import { Node } from "reactflow";
import { Button } from "@mui/joy";
import CodeEditorModal from "$lib/shared/components/Modals/CodeEditorModal";

type Props = {
    node: Node;
    attribute: string;
};

export const EditCode: React.FC<Props> = ({ node, attribute }) => {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [code, setCode] = useState(node.data[attribute] || "def custom_code(active_process: ActiveProcess):\n    pass");
    const { diagram } = useDiagramStore();

    const handleOpenModal = () => setIsModalOpen(true);
    const handleCloseModal = () => setIsModalOpen(false);

    const handleSaveCode = (updatedCode: string) => {
        setCode(updatedCode);
        partialUpdateNode(diagram, node.id, {
            cls: {
                ...node.data,
                [attribute]: updatedCode,
            },
        });
        handleCloseModal();
    };

    return (
        <div className="flex w-full flex-col gap-2 font-mono">
            <span className="w-full border-b border-solid border-gray-400 py-1 font-mono text-xs">
                Edit Code
            </span>
            <Button
                variant="outlined"
                color="primary"
                onClick={handleOpenModal}
                className="w-full"
            >
                Open Code Editor
            </Button>
            <CodeEditorModal
                open={isModalOpen}
                onClose={handleCloseModal}
                onSave={handleSaveCode}
                initialCode={code ||  "def custom_code(active_process: ActiveProcess) -> None:\n    pass"}
            />
        </div>
    );
};

export default EditCode;