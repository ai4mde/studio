import { partialUpdateNode } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";
import { Button } from "@mui/joy";
import { isEqualWith } from "lodash";
import React, { useMemo, useState } from "react";
import { Node } from "reactflow";
import EditMethod from "./EditMethod";
import style from "./editmethods.module.css";

type Props = {
    node: Node;
};

const EditMethods: React.FC<Props> = ({ node }) => {
    const [methods, setMethods] = useState(node?.data?.methods ?? []);
    const { diagram } = useDiagramStore();
    const dirty = useMemo(
        () => !isEqualWith(methods, node?.data?.methods),
        [methods, node?.data?.methods],
    );

    return (
        <div className={style.methods}>
            <span className="w-full border-b border-solid border-gray-400 py-1 text-xs">
                Methods
            </span>

            {methods.map((e: any, idx: number) => (
                <EditMethod
                    key={`method-${idx}`}
                    method={e}
                    update={(v) => {
                        setMethods((s: any[]) => {
                            s[idx] = v;
                            return [...s];
                        });
                    }}
                    del={() => {
                        setMethods((s: any[]) => {
                            return [...s.filter((_, i) => i != idx)];
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
                        setMethods((s: any) => {
                            s.push({
                                type: "str",
                            });
                            return [...s];
                        })
                    }
                >
                    Add Method
                </Button>
                <Button
                    disabled={!dirty}
                    color="primary"
                    className="w-full"
                    size="sm"
                    onClick={() =>
                        partialUpdateNode(diagram, node.id, {
                            cls: {
                                methods: methods,
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

export default EditMethods;
