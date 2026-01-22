import { authAxios } from "$lib/features/auth/state/auth";
import SystemLayout from "$lib/features/browser/components/systems/SystemLayout";
import { queryClient } from "$lib/shared/hooks/queryClient";
import { LinearProgress, Modal, ModalClose, ModalDialog, Divider, Button } from "@mui/joy";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Component, Network, Plus, User, Workflow, Blocks, X, Download } from "lucide-react";
import React, { useState } from "react";
import { useParams } from "react-router";
import { ShowMetadata } from "$metadata/components/ShowMetadata";

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
    const [showModal, setShowModal] = useState(false);
    const [showDeleteDiagramModal, setShowDeleteDiagramModal] = useState(false);
    const [diagramToDelete, setDiagramToDelete] = useState("");

    const system = useQuery<SystemOut>({
        queryKey: [`system`, `${systemId}`],
        queryFn: async () => {
            return (await authAxios.get(`/v1/metadata/systems/${systemId}/`))
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

    const handleExportSystem = async () => {
        const response = await authAxios.get(`/v1/metadata/systems/export/${systemId}/`);
        const jsonStr = JSON.stringify(response.data, null, 2);
        const blow = new Blob([jsonStr], { type: "application/json" });
        const url = URL.createObjectURL(blow);

        const link = document.createElement("a");
        link.href = url;
        link.download = `${system.data?.name ?? "system"}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }

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

    const showMetadata = () => {
        setShowModal(true);
    };

    const closeMetadata = () => {
        setShowModal(false);
    };

    const handleDeleteDiagram = async (diagramId: string) => {
        try {
            await authAxios.delete(`/v1/diagram/${diagramId}/`);
        } catch (error) {
            console.error('Error deleting diagram:', error);
        } finally {
            setDiagramToDelete("");
            setShowDeleteDiagramModal(false);
            queryClient.invalidateQueries({
                queryKey: [`system`, `${systemId}`],
            });
        }
    }

    const openDeleteDiagramModal = (diagramId: string) => {
        setShowDeleteDiagramModal(true);
        setDiagramToDelete(diagramId);
    }
    
    return (
        <>
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
                                            <div className="relative">
                                                <a
                                                    href={`/diagram/${id}`}
                                                    className="flex h-fit flex-col gap-2 rounded-md bg-stone-200 p-4 hover:bg-stone-300"
                                                >
                                                    <h3 className="text-lg">{name}</h3>
                                                    <span className="text-xs">
                                                        {id.split("-").slice(-1)}
                                                    </span>
                                                </a>
                                                <button
                                                    onClick={() => openDeleteDiagramModal(id)}
                                                    className="absolute top-1 right-1 text-gray-500 hover:text-red-500"
                                                >
                                                    <X />
                                                </button>
                                            </div>
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
                            <button
                                className="flex h-full w-full items-center justify-center gap-1 rounded-md bg-stone-100 p-4 hover:bg-stone-200"
                                onClick={() => showMetadata()}
                            >
                                <Blocks size={16}/>
                                <h2 className="text-base">Show Metadata</h2>
                            </button>
                            <button
                                className="flex h-full w-full items-center justify-center gap-1 rounded-md bg-stone-100 p-4 hover:bg-stone-200"
                                onClick={() => handleExportSystem()}
                            >
                                <Download size={16}/>
                                <h2 className="text-base">Export System</h2>
                            </button>
                            
                        </div>
                    </>
                )}
            </SystemLayout>
            <Modal
                open={showModal}
                onClose={closeMetadata}
            >
                <ModalDialog className="max-h-screen overflow-y-auto">
                    <ModalClose
                        sx={{
                            position: "relative",
                        }}
                    />
                    <div className="flex h-full w-full flex-col gap-1 p-3">
                        <ShowMetadata systemId={systemId} />
                    </div>
                </ModalDialog>
            </Modal>
            <Modal
                open={showDeleteDiagramModal}
                onClose={() => setShowDeleteDiagramModal(false)}
            >
                <ModalDialog>
                    <div className="flex w-full flex-row justify-between pb-1">
                        <div className="flex flex-col">
                            <h1 className="font-bold">Confirm</h1>
                            <h3 className="text-sm">Are you sure you want to delete this diagram?</h3>
                        </div>
                        <ModalClose
                            sx={{
                                position: "relative",
                                top: 0,
                                right: 0,
                            }}
                        />
                    </div>
                    <Divider />
                    <div className="flex flex-row pt-1 gap-4">
                        <Button onClick={() => {setShowDeleteDiagramModal(false); setDiagramToDelete("");}} variant="outlined" color="neutral">
                            Cancel
                        </Button>
                        <Button onClick={() => handleDeleteDiagram(diagramToDelete)} variant="solid" color="danger">
                            Confirm
                        </Button>
                    </div>
                </ModalDialog>
            </Modal>
        </>
    );
};

export default SystemDiagrams;
