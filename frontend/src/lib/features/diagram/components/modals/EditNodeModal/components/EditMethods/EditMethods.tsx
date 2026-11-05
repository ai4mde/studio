import { Button } from "@mui/joy";
import { isEqualWith } from "lodash";
import React, { useEffect, useMemo, useState } from "react";
import { Node } from "reactflow";
import { useOperations, useSaveOperations } from "../../../../../../../../api/metadata/hooks/classMembers";
import EditMethod from "./EditMethod";
import style from "./editmethods.module.css";

type Props = {
    node: Node;
};

const EditMethods: React.FC<Props> = ({ node }) => {
    const classifierId = node?.data?.classifierId;
    const { data: serverMethods = [], isSuccess } = useOperations(classifierId);
    const saveMethods = useSaveOperations(classifierId);

    const [methods, setMethods] = useState<any[]>([]);

    // Start editing from what the server has, and again after every save
    useEffect(() => {
        if (isSuccess) setMethods(serverMethods.map((m) => ({ ...m })));
    }, [isSuccess, serverMethods]);

    const dirty = useMemo(
        () => !isEqualWith(methods, serverMethods),
        [methods, serverMethods],
    );

    return (
        <div className={style.methods}>
            <span className="w-full border-b border-solid border-gray-400 py-1 text-xs">
                Methods
            </span>

            {methods.map((e: any, idx: number) => (
                <EditMethod
                    key={`method-${idx}`}
                    node={node}
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
                                type: "string",
                            });
                            return [...s];
                        })
                    }
                >
                    Add Method
                </Button>
                <Button
                    disabled={!dirty || saveMethods.isPending}
                    color="primary"
                    className="w-full"
                    size="sm"
                    onClick={() =>
                        saveMethods.mutate({
                            original: serverMethods,
                            edited: methods,
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
