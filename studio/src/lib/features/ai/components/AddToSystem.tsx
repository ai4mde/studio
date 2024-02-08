import { Card } from "@mui/joy";
import React from "react";
import { Pipeline } from "../types";
import { PreviewNode } from "$diagram/components/core/Node/Node";
import { ArrowRight } from "lucide-react";

type Props = {
    pipeline: Pipeline;
};

export const AddToSystem: React.FC<Props> = ({ pipeline }) => {
    const [classifiers, setClassifiers] = React.useState<any[]>([]);
    const [relations, setRelations] = React.useState<any[]>([]);

    const _classifiers = pipeline?.output?.classifiers || [];
    const _relations = pipeline?.output?.relations || [];

    const toggleClassifier = (id: string) => {
        if (classifiers.includes(id)) {
            setClassifiers(classifiers.filter((c) => c !== id));
            setRelations(
                relations.filter((r) => {
                    const relation = _relations.find((rel: any) => rel.id == r);
                    return (
                        relation.data.source !== id &&
                        relation.data.target !== id
                    );
                }),
            );
        } else {
            setClassifiers([...classifiers, id]);
        }
    };

    const toggleRelation = (id: string, source: string, target: string) => {
        if (relations.includes(id)) {
            setRelations(relations.filter((c) => c !== id));
        } else {
            setRelations([...relations, id]);
            setClassifiers([...classifiers, source, target]);
        }
    };

    return (
        <Card className="flex w-full flex-col gap-4 p-4">
            <div className="flex w-full flex-col gap-1">
                <span>Classifiers</span>
                <div className="flex flex-row items-center gap-2">
                    {_classifiers.map((classifier: any) => (
                        <button
                            className={[
                                "border p-1",
                                classifiers.includes(classifier.id)
                                    ? "bg-blue-300 hover:bg-red-200"
                                    : "bg-stone-100 hover:bg-stone-200",
                            ].join(" ")}
                            onClick={() => toggleClassifier(classifier.id)}
                        >
                            <PreviewNode
                                type={classifier.data.type}
                                data={classifier.data}
                                id={classifier.id}
                                selected={false}
                                zIndex={0}
                                isConnectable={false}
                                xPos={0}
                                yPos={0}
                                dragging={false}
                            />
                        </button>
                    ))}
                </div>
            </div>
            <div className="flex w-full flex-col gap-1">
                <span>Relations</span>
                <div className="flex flex-row flex-wrap items-center gap-2">
                    {_relations.map((relation: any) => (
                        <span>
                            {[""].map(() => {
                                const source = _classifiers.find(
                                    (e: any) => e.id == relation.data.source,
                                );
                                const target = _classifiers.find(
                                    (e: any) => e.id == relation.data.target,
                                );

                                if (!source || !target) {
                                    return <></>;
                                }

                                return (
                                    <button
                                        className={[
                                            "flex w-full flex-row items-center justify-between gap-2 border p-1",
                                            relations.includes(relation.id)
                                                ? "bg-blue-300 hover:bg-red-200"
                                                : "bg-stone-100 hover:bg-stone-200",
                                        ].join(" ")}
                                        onClick={() =>
                                            toggleRelation(
                                                relation.id,
                                                relation.data.source,
                                                relation.data.target,
                                            )
                                        }
                                    >
                                        <span>
                                            {source && (
                                                <PreviewNode
                                                    type={source?.data.type}
                                                    data={source?.data}
                                                    id={""}
                                                    selected={false}
                                                    zIndex={0}
                                                    isConnectable={false}
                                                    xPos={0}
                                                    yPos={0}
                                                    dragging={false}
                                                />
                                            )}
                                        </span>
                                        <ArrowRight size={18} />
                                        {relation.data.type}
                                        <ArrowRight size={18} />
                                        <span>
                                            {target && (
                                                <PreviewNode
                                                    type={target?.data.type}
                                                    data={target?.data}
                                                    id={""}
                                                    selected={false}
                                                    zIndex={0}
                                                    isConnectable={false}
                                                    xPos={0}
                                                    yPos={0}
                                                    dragging={false}
                                                />
                                            )}
                                        </span>
                                    </button>
                                );
                            })}
                        </span>
                    ))}
                </div>
            </div>
        </Card>
    );
};
