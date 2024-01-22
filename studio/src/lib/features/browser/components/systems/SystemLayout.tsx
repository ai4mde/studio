import { AppWindow, Blocks, Component, GitGraph } from "lucide-react";
import React from "react";
import { matchPath, useLocation, useParams } from "react-router";

type Props = {
    children?: React.ReactNode;
};

const TopNavigation: React.FC = () => {
    const { systemId } = useParams();
    const { pathname } = useLocation();

    const navigation = [
        {
            name: "Diagrams",
            Icon: GitGraph,
            href: `/systems/${systemId}`,
            strict: true,
        },
        {
            name: "Repository",
            Icon: Blocks,
            href: `/systems/${systemId}/repository`,
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
    ];

    return (
        <div className="w-full h-10 flex flex-row items-stretch font-semibold bg-gray-100 text-sm text-stone-700">
            {navigation.map(({ name, Icon, href, strict }) => (
                <>
                    <a
                        className={[
                            "flex flex-row gap-2 px-3 items-center border-b border-transparent hover:text-stone-900 hover:bg-stone-200",
                            (strict
                                ? pathname == href
                                : matchPath(href, pathname)) &&
                                "bg-stone-200 text-stone-900 !border-stone-900",
                        ]
                            .filter(Boolean)
                            .join(" ")}
                        href={href}
                    >
                        <Icon size={14} />
                        {name}
                    </a>
                </>
            ))}
        </div>
    );
};

const SystemLayout: React.FC<Props> = ({ children }) => {
    return (
        <div
            className="w-full h-full grid grid-cols-12 items-center"
            style={{
                gridTemplateRows: "fit-content(4rem) 1fr fit-content(4rem)",
            }}
        >
            <div className="col-span-12">
                <TopNavigation />
            </div>

            <div className="col-span-12 h-full">{children}</div>

            <div className="col-span-12 flex flex-row p-3">AI4MDE</div>
        </div>
    );
};

export default SystemLayout;
