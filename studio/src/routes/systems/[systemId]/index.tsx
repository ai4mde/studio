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
    diagrams_by_type?: {
        classes?: FlatDiagram[];
        usecase?: FlatDiagram[];
        activity?: FlatDiagram[];
        component?: FlatDiagram[];
    };
};

type NewDiagram = {
    type: string;
    name: string;
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
                type: type,
            });
            queryClient.refetchQueries({
                queryKey: [`system`, `${systemId}`],
            });
        },
    });

    const { diagrams_by_type } = system.data ?? {};
    const uiDiagrams = [
        {
            type: "classes",
            name: "Class Diagram",
            Icon: Network,
            diagrams: diagrams_by_type?.classes ?? [],
        },
        {
            type: "activity",
            name: "Activity Diagram",
            Icon: Workflow,
            diagrams: diagrams_by_type?.activity ?? [],
        },
        {
            type: "usecase",
            name: "Usecase Diagram",
            Icon: User,
            diagrams: diagrams_by_type?.usecase ?? [],
        },
        {
            type: "component",
            name: "Component Diagram",
            Icon: Component,
            diagrams: diagrams_by_type?.component ?? [],
        },
    ];

    return (
        <SystemLayout>
            {system.isLoading && (
                <LinearProgress className="absolute left-0 right-0 top-0" />
            )}
            {system.isSuccess && (
                <>
                    <div className="flex flex-col gap-3 p-3">
                        {uiDiagrams.map(({ name, Icon, diagrams, type }) => (
                            <>
                                <span className="flex flex-row items-center gap-2">
                                    <Icon size={24} />
                                    <h1 className="text-lg">{name}</h1>
                                </span>
                                <div className="flex flex-row flex-nowrap gap-2 rounded-md bg-stone-100 p-2">
                                    {diagrams.map(({ id, name }) => (
                                        <a
                                            href={`/diagram/${id}`}
                                            className="flex h-fit flex-col gap-2 rounded-md bg-stone-200 p-4 hover:bg-stone-300"
                                        >
                                            <h3 className="text-lg">{name}</h3>
                                            <span className="text-xs">
                                                {id.split("-").slice(-1)}
                                            </span>
                                        </a>
                                    ))}
                                    <button
                                        onClick={() =>
                                            newDiagram.mutate({
                                                type: type,
                                                name: name,
                                            })
                                        }
                                        className="flex h-full flex-col gap-2 rounded-md bg-stone-200 p-4 hover:bg-stone-300"
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
