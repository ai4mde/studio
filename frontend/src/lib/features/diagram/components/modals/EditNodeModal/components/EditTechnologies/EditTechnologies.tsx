import { partialUpdateNode } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";
import { Button, FormLabel, Stack } from "@mui/joy";
import { isEqualWith } from "lodash";
import React, { useMemo, useState } from "react";
import { Node } from "reactflow";
import EditTechnology from "./EditTechnology";

type Props = {
    node: Node;
};

const EditTechnologies: React.FC<Props> = ({ node }) => {
    const [technologies, setTechnologies] = useState(node?.data?.technologies ?? []);
    const { diagram } = useDiagramStore();
    
    const dirty = useMemo(
        () => !isEqualWith(technologies, node?.data?.technologies),
        [technologies, node?.data?.technologies],
    );

    return (
        <Stack spacing={1}>
            <span className="w-full border-b border-solid border-gray-400 py-1 text-xs">
                Technologies
            </span>
            <Stack spacing={1}>
                {technologies.map((tech: string, idx: number) => (
                    <EditTechnology
                        key={`technology-${idx}`}
                        technology={tech}
                        update={(v) => {
                            setTechnologies((s: string[]) => {
                                s[idx] = v;
                                return [...s];
                            });
                        }}
                        del={() => {
                            setTechnologies((s: string[]) => {
                                return [...s.filter((_, i) => i !== idx)];
                            });
                        }}
                        node={node}
                    />
                ))}
            </Stack>

            <Stack direction="row" spacing={1}>
                <Button
                    color="success"
                    className="w-full"
                    size="sm"
                    variant="outlined"
                    onClick={() =>
                        setTechnologies((s: string[]) => {
                            return [...s, ""];
                        })
                    }
                >
                    Add Technology
                </Button>
                <Button
                    disabled={!dirty}
                    color="primary"
                    size="sm"
                    onClick={() =>
                        partialUpdateNode(diagram, node.id, {
                            cls: {
                                technologies: technologies,
                            },
                        })
                    }
                >
                    Save
                </Button>
            </Stack>
        </Stack>
    );
};

export default EditTechnologies;
