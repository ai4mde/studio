import { useAuthStore } from "$lib/features/auth/state/auth";
import { Bot, Box, LayoutDashboard, List, LogOut, User } from "lucide-react";
import React from "react";
import { useLocation } from "react-router-dom";

export const Navigation: React.FC = () => {
    const { pathname } = useLocation();
    const { isAuthenticated, logout } = useAuthStore();

    const linkClassName =
        "flex items-center justify-between hover:text-gray-800 " +
        "flex-row gap-3 p-3 pr-4 box-border hover:bg-gray-200 " +
        "hover:border-l-blue-700 border-l-4 border-solid";

    const activeLink = "text-gray-800 bg-gray-200 border-l-blue-700";
    const inactiveLink = "text-gray-600 bg-transparent border-l-transparent";

    return (
        <div className="flex flex-col left-0 bottom-0 top-12 fixed z-10 overflow-x-hidden w-12 hover:w-48 transition-all bg-gray-100">
            <div className="flex flex-col w-48 h-full pb-4">
                <a
                    className={
                        linkClassName +
                        " " +
                        (pathname == "/" ? activeLink : inactiveLink)
                    }
                    href="/"
                >
                    <LayoutDashboard size={20} />
                    <span className="font-bold text-sm">Dashboard</span>
                </a>
                <a
                    className={
                        linkClassName +
                        " " +
                        (pathname.startsWith("/build")
                            ? activeLink
                            : inactiveLink)
                    }
                    href="/build/"
                >
                    <Bot size={20} />
                    <span className="font-bold text-sm">Build</span>
                </a>
                <a
                    className={
                        linkClassName +
                        " " +
                        (pathname.startsWith("/projects") ||
                        pathname.startsWith("/systems") ||
                        pathname.startsWith("/diagram")
                            ? activeLink
                            : inactiveLink)
                    }
                    href="/projects/"
                >
                    <Box size={20} />
                    <span className="font-bold text-sm">Projects</span>
                </a>
                <a
                    className={
                        linkClassName +
                        " " +
                        (pathname.startsWith("/libraries")
                            ? activeLink
                            : inactiveLink)
                    }
                    href="/libraries/"
                >
                    <List size={20} />
                    <span className="font-bold text-sm">Libraries</span>
                </a>
                {isAuthenticated && (
                    <div className="flex flex-col mt-auto">
                        {/* This button can be enabled when
                            account functionality is added */}
                        {/*<a
                            className={
                                linkClassName +
                                " " +
                                (pathname.startsWith("/account")
                                    ? activeLink
                                    : inactiveLink)
                            }
                            href="/account/"
                        >
                            <User size={20} />
                            <span className="font-bold text-sm">Account</span>
                        </a>*/}
                        <button
                            className={linkClassName}
                            onClick={() => logout()}
                        >
                            <LogOut size={20} />
                            <span className="font-bold text-sm">Logout</span>
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Navigation;
