import { partialUpdateNode } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";
import { useSystemObjectClassifiers } from "$diagram/components/modals/ImportNodeModal/queries/importNode";
import Chip from "@mui/joy/Chip";
import { Save } from "lucide-react";
import React, { useState } from "react";
import { Node } from "reactflow";

type Props = { node: Node };

export const EditActionClasses: React.FC<Props> = ({ node }) => {
    const { diagram, systemId } = useDiagramStore();
    const [classClassifiers, ok] = useSystemObjectClassifiers(systemId);

    const initialInput = (node.data?.classes?.input ?? []) as string[];
    const initialOutput = (node.data?.classes?.output ?? []) as string[];

    const [inputIds, setInputIds] = useState<string[]>(initialInput);
    const [outputIds, setOutputIds] = useState<string[]>(initialOutput);

    const dirty =
        JSON.stringify([...inputIds].sort()) !== JSON.stringify([...initialInput].sort()) ||
        JSON.stringify([...outputIds].sort()) !== JSON.stringify([...initialOutput].sort());

    const toggle = (
        ids: string[],
        setIds: React.Dispatch<React.SetStateAction<string[]>>,
        id: string,
    ) => {
        setIds((prev) =>
            prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
        );
    };

    const handleSave = () => {
        partialUpdateNode(diagram, node.id, {
            cls: { classes: { input: inputIds, output: outputIds } },
        });
    };

    if (!ok || !classClassifiers.length) return null;

    return (
        <div className="flex w-full flex-col gap-2 font-mono">
            <span className="w-full border-b border-solid border-gray-400 py-1 font-mono text-xs">
                Input / Output Classes
            </span>
            <div className="flex flex-col gap-2">
                <span className="text-xs text-gray-500">Input classes</span>
                <div className="flex flex-wrap gap-1">
                    {classClassifiers.map((cls) => (
                        <Chip
                            key={cls.id}
                            size="sm"
                            onClick={() => toggle(inputIds, setInputIds, String(cls.id))}
                            color={inputIds.includes(String(cls.id)) ? "primary" : "neutral"}
                        >
                            {cls.data?.name}
                        </Chip>
                    ))}
                </div>
                <span className="text-xs text-gray-500">Output classes</span>
                <div className="flex flex-wrap gap-1">
                    {classClassifiers.map((cls) => (
                        <Chip
                            key={cls.id}
                            size="sm"
                            onClick={() => toggle(outputIds, setOutputIds, String(cls.id))}
                            color={outputIds.includes(String(cls.id)) ? "success" : "neutral"}
                        >
                            {cls.data?.name}
                        </Chip>
                    ))}
                </div>
            </div>
            <button
                onClick={handleSave}
                disabled={!dirty}
                className="flex items-center gap-1 self-end text-xs text-blue-500 disabled:text-gray-300"
            >
                <Save size={12} /> Save
            </button>
        </div>
    );
};

export default EditActionClasses;
