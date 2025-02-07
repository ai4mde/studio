import { partialUpdateNode } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";
import { Save } from "lucide-react";
import React, { useState, useEffect } from "react";
import { Node } from "reactflow";
import { RelatedNode } from "$diagram/types/diagramState";
import style from "./editswimlaneactor.module.css";

type Props = {
    node: Node;
    uniqueActors: RelatedNode[];
}

const Button: React.FC<any> = ({ dirty }) => {
    return (
        <button type="submit" className={style.save} disabled={!dirty}>
            <Save size={12} />
        </button>
    );
};

export const EditSwimlaneActor: React.FC<Props> = ({ node, uniqueActors }) => {
    const [actorNode, setActorNode] = useState(node.data["actorNode"]);
    const { diagram } = useDiagramStore();

    const handleSubmit: React.FormEventHandler<HTMLFormElement> = (e) => {
        e.preventDefault();
        partialUpdateNode(diagram, node.id, {
            cls: {
                actorNode: actorNode,
            },
        });
    };

    return (
        <div className="flex w-full flex-col gap-2 font-mono">
            <span className="w-full border-b border-solid border-gray-400 py-1 font-mono text-xs">
                Actor Node
            </span>
            <form
                className={[
                    style.editswimlaneactor,
                    actorNode != node.data["actorNode"] && style.dirty,
                ]
                    .filter(Boolean)
                    .join(" ")}
                onSubmit={handleSubmit}
            >
                <div className="flex items-center justify-between w-full">
                    <div className="flex items-stretch">
                        <select
                            value={actorNode}
                            onChange={(e) => setActorNode(e.target.value)}
                            className="h-full"
                        >
                            {uniqueActors.map((actor) => (
                                <option key={actor.id} value={actor.id}>
                                    {actor.name}
                                </option>
                            ))}
                        </select>
                    </div>
                    <Button dirty={actorNode != node.data["actorNode"]} />
                </div>
            </form>
        </div>
    );
};

export default EditSwimlaneActor;