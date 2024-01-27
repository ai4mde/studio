import { partialUpdateNode } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";
import { Button } from "@mui/joy";
import { isEqualWith } from "lodash";
import React, { useMemo, useState } from "react";
import { Node } from "reactflow";
import EditAttribute from "./EditAttribute";
import style from "./editattributes.module.css";

type Props = {
    node: Node;
};

const EditAttributes: React.FC<Props> = ({ node }) => {
    const [attributes, setAttributes] = useState(node?.data?.attributes ?? []);
    const { diagram } = useDiagramStore();
    const dirty = useMemo(
        () => !isEqualWith(attributes, node?.data?.attributes),
        [attributes, node?.data?.attributes]
    );

    return (
        <div className={style.attributes}>
            <span className="text-xs py-1 w-full border-b border-solid border-gray-400">
                Attributes
            </span>

            {attributes.map((e: any, idx: number) => (
                <EditAttribute
                    key={`attribute-${idx}`}
                    attribute={e}
                    update={(v) => {
                        setAttributes((s: any[]) => {
                            s[idx] = v;
                            return [...s];
                        });
                    }}
                    del={() => {
                        setAttributes((s: any[]) => {
                            return [...s.filter((_, i) => i != idx)];
                        });
                    }}
                />
            ))}

            <div className="flex flex-row justify-stretch items-center gap-2">
                <Button
                    color="success"
                    className="w-full"
                    size="sm"
                    variant="outlined"
                    onClick={() =>
                        setAttributes((s: any) => {
                            s.push({
                                type: "str",
                            });
                            return [...s];
                        })
                    }
                >
                    Add Attribute
                </Button>
                <Button
                    disabled={!dirty}
                    color="primary"
                    className="w-full"
                    size="sm"
                    onClick={() =>
                        partialUpdateNode(diagram, node.id, {
                            data: {
                                attributes: attributes,
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

export default EditAttributes;
