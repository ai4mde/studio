import { Button } from "@mui/joy";
import { isEqualWith } from "lodash";
import React, { useMemo, useState, useEffect } from "react";
import { Node } from "reactflow";
import EditAttribute from "./EditAttribute";
import { useAttributes, useSaveAttributes } from "../../../../../../../../api/metadata/hooks/classMembers";
import style from "./editattributes.module.css";

type Props = {
    node: Node;
};

const EditAttributes: React.FC<Props> = ({ node }) => {
    const classifierId = node?.data?.classifierId;
    const { data: serverAttributes = [], isSuccess } = useAttributes(classifierId);
    const saveAttributes = useSaveAttributes(classifierId);

    const [attributes, setAttributes] = useState<any[]>([]);

    // Start editing from what the server has, and again after every save
    useEffect(() => {
        if (isSuccess) setAttributes(serverAttributes.map((a) => ({ ...a })));
    }, [isSuccess, serverAttributes]);

    const dirty = useMemo(
        () => !isEqualWith(attributes, serverAttributes),
        [attributes, serverAttributes],
    );

    return (
        <div className={style.attributes}>
            <span className="w-full border-b border-solid border-gray-400 py-1 text-xs">
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
                    node={node}
                />
            ))}

            <div className="flex flex-row items-center justify-stretch gap-2">
                <Button
                    color="success"
                    className="w-full"
                    size="sm"
                    variant="outlined"
                    onClick={() =>
                        setAttributes((s: any) => {
                            s.push({
                                type: "string",
                                enum: null,
                                derived: false,
                            });
                            return [...s];
                        })
                    }
                >
                    Add Attribute
                </Button>
                <Button
                    color="primary"
                    className="w-full"
                    size="sm"
                    disabled={!dirty || saveAttributes.isPending}
                    onClick={() =>
                        saveAttributes.mutate({
                            original: serverAttributes,
                            edited: attributes,
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
