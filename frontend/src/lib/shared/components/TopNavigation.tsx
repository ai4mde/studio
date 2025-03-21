import { ArrowLeft, LucideIcon } from "lucide-react";
import React from "react";
import { matchPath, useLocation } from "react-router";

type Props = {
    back?: string;
    navigation?: {
        name: string;
        Icon: LucideIcon;
        href: string;
        strict?: boolean;
    }[];
};

export const TopNavigation: React.FC<Props> = ({ back, navigation }) => {
    const { pathname } = useLocation();

    return (
        <div className="w-full h-10 flex flex-row items-stretch font-semibold bg-gray-100 text-sm text-stone-700">
            {back && (
                <a
                    className="flex flex-row items-center px-3 border-b border-transparent hover:text-stone-900 hover:bg-stone-200"
                    href={back}
                >
                    <ArrowLeft size={18} />
                </a>
            )}
            {navigation?.map(({ name, Icon, href, strict }) => (
                    <a
                        key={href}
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
            ))}
        </div>
    );
};
