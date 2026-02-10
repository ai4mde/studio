import { useSystem } from "$browser/queries";
import { TopNavigation } from "$lib/shared/components/TopNavigation";
import { GitGraph, Package, PaintRoller, Rocket } from "lucide-react";
import React from "react";
import { useParams } from "react-router";

type Props = {
    children?: React.ReactNode;
};

const SystemLayout: React.FC<Props> = ({ children }) => {
    const { systemId } = useParams();
    const { data } = useSystem(systemId);

    return (
        <div
            className="grid h-full w-full grid-cols-12 items-center"
            style={{
                gridTemplateRows: "fit-content(4rem) 1fr fit-content(4rem)",
            }}
        >
            <div className="col-span-12">
                <TopNavigation
                    back={
                        data?.project
                            ? `/projects/${data.project}`
                            : "/projects/"
                    }
                    navigation={[
                        {
                            name: "Diagrams",
                            Icon: GitGraph,
                            href: `/systems/${systemId}`,
                            strict: true,
                        },
                        {
                            name: "Interfaces",
                            Icon: PaintRoller,
                            href: `/systems/${systemId}/interfaces`,
                        },
                        {
                            name: "Prototypes",
                            Icon: Package,
                            href: `/systems/${systemId}/prototypes`,
                        },
                        {
                            name: "Versions",
                            Icon: Rocket,
                            href: `/systems/${systemId}/versions`,
                            strict: true,
                        },
                    ]}
                />
            </div>

            <div className="col-span-12 h-full">{children}</div>
            <div className="col-span-12 flex flex-row p-3">AI4MDE</div>
        </div>
    );
};

export default SystemLayout;
