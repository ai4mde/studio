import { TopNavigation } from "$lib/shared/components/TopNavigation";
import { AppWindow, Blocks, Component, GitGraph, User } from "lucide-react";
import React from "react";
import { useParams } from "react-router";

type Props = {
    children?: React.ReactNode;
};

const SystemLayout: React.FC<Props> = ({ children }) => {
    const { systemId } = useParams();

    return (
        <div
            className="w-full h-full grid grid-cols-12 items-center"
            style={{
                gridTemplateRows: "fit-content(4rem) 1fr fit-content(4rem)",
            }}
        >
            <div className="col-span-12">
                <TopNavigation
                    back="/projects"
                    navigation={[
                        {
                            name: "Diagrams",
                            Icon: GitGraph,
                            href: `/systems/${systemId}`,
                            strict: true,
                        },
                        {
                            name: "Metadata",
                            Icon: Blocks,
                            href: `/systems/${systemId}/metadata`,
                        },
                        {
                            name: "Applications",
                            Icon: AppWindow,
                            href: `/systems/${systemId}/applications`,
                        },
                        {
                            name: "Components",
                            Icon: Component,
                            href: `/systems/${systemId}/components`,
                        },
                        {
                            name: "Users",
                            Icon: User,
                            href: `/systems/${systemId}/users`,
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
