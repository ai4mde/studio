import { authAxios } from "$lib/features/auth/state/auth";
import SystemLayout from "$lib/features/browser/components/systems/SystemLayout";
import { queryClient } from "$lib/shared/hooks/queryClient";
import { LinearProgress } from "@mui/joy";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Component, Network, Plus, User, Workflow } from "lucide-react";
import React from "react";
import { useParams } from "react-router";

type FlatDiagram = {
    id: string;
    name: string;
    description: string;
};

type SystemOut = {
    id: string;
    name: string;
    description?: string;
    diagrams?: {
        classes?: FlatDiagram[];
        usecase?: FlatDiagram[];
        activity?: FlatDiagram[];
        component?: FlatDiagram[];
    };
};

type NewDiagram = {
    type: string;
};

const SystemDiagrams: React.FC = () => {
    const { systemId } = useParams();

    const system = useQuery<SystemOut>({
        queryKey: [`system`, `${systemId}`],
        queryFn: async () => {
            return (await authAxios.get(`/v1/metadata/systems/${systemId}`))
                .data;
        },
        enabled: !!systemId,
    });

    const newDiagram = useMutation<unknown, unknown, NewDiagram>({
        mutationFn: async ({ type }) => {
            await authAxios.post(`/v1/diagram/`, {
                system: systemId,
                diagram: type,
            });
            queryClient.refetchQueries({
                queryKey: [`system`, `${systemId}`],
            });
        },
    });

    const { diagrams } = system.data ?? {};
    const uiDiagrams = [
        {
            type: "classes",
            name: "Class Diagrams",
            Icon: Network,
            diagrams: diagrams?.classes ?? [],
        },
        {
            type: "activity",
            name: "Activity Diagrams",
            Icon: Workflow,
            diagrams: diagrams?.activity ?? [],
        },
        {
            type: "usecase",
            name: "Usecase Diagrams",
            Icon: User,
            diagrams: diagrams?.usecase ?? [],
        },
        {
            type: "component",
            name: "Component Diagrams",
            Icon: Component,
            diagrams: diagrams?.component ?? [],
        },
    ];

    return (
        <SystemLayout>
            {system.isLoading && (
                <LinearProgress className="absolute top-0 left-0 right-0" />
            )}
            {system.isSuccess && (
                <>
                    <div className="flex flex-col gap-3 p-3">
                        {uiDiagrams.map(({ name, Icon, diagrams, type }) => (
                            <>
                                <span className="flex flex-row gap-2 items-center">
                                    <Icon size={24} />
                                    <h1 className="text-lg">{name}</h1>
                                </span>
                                <div className="flex flex-row flex-nowrap rounded-md bg-stone-100 p-2 gap-2 ">
                                    {diagrams.map(({ id, name }) => (
                                        <a
                                            href={`/diagram/${id}`}
                                            className="flex flex-col gap-2 p-4 rounded-md bg-stone-200 hover:bg-stone-300 h-fit"
                                        >
                                            <h3 className="text-lg">{name}</h3>
                                            <span className="text-xs">
                                                {id.split("-").slice(-1)}
                                            </span>
                                        </a>
                                    ))}
                                    <button
                                        onClick={() =>
                                            newDiagram.mutate({ type: type })
                                        }
                                        className="flex flex-col gap-2 p-4 rounded-md bg-stone-200 hover:bg-stone-300 h-full"
                                    >
                                        <Plus />
                                    </button>
                                </div>
                            </>
                        ))}
                    </div>
                </>
            )}
        </SystemLayout>
    );
};

export default SystemDiagrams;
