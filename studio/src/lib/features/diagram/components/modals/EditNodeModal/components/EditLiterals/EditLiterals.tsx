import { partialUpdateNode } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";
import { Button } from "@mui/joy";
import { isEqualWith } from "lodash";
import React, { useMemo, useState } from "react";
import { Node } from "reactflow";
import EditLiteral from "./EditLiteral";
import style from "./editliterals.module.css";

type Props = {
    node: Node;
};

const EditLiterals: React.FC<Props> = ({ node }) => {
    const [literals, setLiterals] = useState(node?.data?.literals ?? []);
    const { diagram } = useDiagramStore();
    const dirty = useMemo(
        () => !isEqualWith(literals, node?.data?.literals),
        [literals, node?.data?.literals],
    );

    return (
        <div className={style.attributes}>
            <span className="w-full border-b border-solid border-gray-400 py-1 text-xs">
                Literals
            </span>

            {literals.map((e: any, idx: number) => (
                <EditLiteral
                    key={`literal-${idx}`}
                    literal={e}
                    update={(v) => {
                        setLiterals((s: any[]) => {
                            s[idx] = v;
                            return [...s];
                        });
                    }}
                    del={() => {
                        setLiterals((s: any[]) => {
                            const _ = s.slice();
                            _.splice(idx, 1);
                            return [..._];
                        });
                    }}
                />
            ))}

            <div className="flex flex-row items-center justify-stretch gap-2">
                <Button
                    color="success"
                    className="w-full"
                    size="sm"
                    variant="outlined"
                    onClick={() =>
                        setLiterals((s: any) => {
                            return [...s, ""];
                        })
                    }
                >
                    Add Literal
                </Button>
                <Button
                    disabled={!dirty}
                    color="primary"
                    className="w-full"
                    size="sm"
                    onClick={() =>
                        partialUpdateNode(diagram, node.id, {
                            cls: {
                                literals: literals,
                            },
                        })
                    }
                >
                    Save
                </Button>
            </div>
        </div>
    );
};

export default EditLiterals;
