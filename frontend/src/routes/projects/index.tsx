import { createProjectAtom } from "$browser/atoms";
import { CreateProject } from "$browser/components/projects/CreateProject";
import { authAxios } from "$lib/features/auth/state/auth";
import { queryClient } from "$lib/shared/hooks/queryClient";
import { TopNavigation } from "$lib/shared/components/TopNavigation";
import { LinearProgress, Modal, ModalClose, ModalDialog, Divider, Button } from "@mui/joy";
import { useQuery } from "@tanstack/react-query";
import { useAtom } from "jotai";
import { Box, Plus, X } from "lucide-react";
import React, { useState } from "react";

type ProjectOut = {
    id: string;
    name: string;
    description?: string;
};

const ProjectsIndex: React.FC = () => {
    const [, setCreate] = useAtom(createProjectAtom);
    const [showDeleteProjectModal, setShowDeleteProjectModal] = useState(false);
    const [projectToDelete, setProjectToDelete] = useState("");

    const { isLoading, isSuccess, data } = useQuery<ProjectOut[]>({
        queryKey: ["projects"],
        queryFn: async () => {
            return (await authAxios.get("/v1/metadata/projects/")).data;
        },
    });

    const handleDeleteProject = async (projectId: string) => {
        try {
            await authAxios.delete(`/v1/metadata/projects/${projectId}`);
        } catch (error) {
            console.error('Error deleting project:', error);
        } finally {
            setProjectToDelete("");
            setShowDeleteProjectModal(false);
            queryClient.invalidateQueries({
                queryKey: [`projects`],
            });
        }
    }

    const openDeleteProjectModal = (projectId: string) => {
        setShowDeleteProjectModal(true);
        setProjectToDelete(projectId);
    }

    return (
        <>
            <CreateProject />
            <div
                className="w-full h-full grid grid-cols-12 items-center"
                style={{
                    gridTemplateRows: "fit-content(4rem) 1fr fit-content(4rem)",
                }}
            >
                <div className="col-span-12">
                    <TopNavigation
                        back="/"
                        navigation={[
                            {
                                name: "Projects",
                                Icon: Box,
                                href: "/projects",
                            },
                        ]}
                    />
                </div>

                <div className="col-span-12 border-t-stone-200 flex flex-row p-3 gap-3 flex-wrap h-full">
                    {isLoading && (
                        <LinearProgress className="absolute top-0 left-0 right-0" />
                    )}

                    <div className="flex flex-col gap-3 w-full">
                        <span className="flex flex-row gap-2 items-center">
                            <Box size={24} />
                            <h1 className="text-lg">Projects</h1>
                        </span>
                        <div className="flex flex-row flex-nowrap rounded-md bg-stone-100 p-2 gap-2 ">
                            {isSuccess &&
                                data.map((e) => (
                                    <div key={e.id} className="relative">
                                        <a
                                            href={`/projects/${e.id}`}
                                            className="flex flex-col gap-2 p-4 w-48 text-ellipsis overflow-hidden rounded-md bg-stone-200 hover:bg-stone-300 h-fit"
                                        >
                                            <h3 className="text-xl font-bold">
                                                {e.name}
                                            </h3>
                                            <h3 className="text-sm">
                                                {e.description}
                                            </h3>
                                            <span className="text-xs text-right pt-2 text-stone-500">
                                                {e.id.split("-").slice(-1)}
                                            </span>
                                        </a>
                                        <button
                                            onClick={() => openDeleteProjectModal(e.id)}
                                            className="absolute top-1 right-1 text-gray-500 hover:text-red-500"
                                        >
                                            <X />
                                        </button>
                                    </div>
                                ))}
                            <button
                                onClick={() => setCreate(true)}
                                className="flex flex-col gap-2 p-4 rounded-md bg-stone-100 hover:bg-stone-200 h-fill items-center justify-center"
                            >
                                <Plus />
                            </button>
                        </div>
                    </div>
                </div>
                <div className="col-span-12 flex flex-row">AI4MDE</div>
            </div>
            <Modal
                open={showDeleteProjectModal}
                onClose={() => setShowDeleteProjectModal(false)}
            >
                <ModalDialog>
                    <div className="flex w-full flex-row justify-between pb-1">
                        <div className="flex flex-col">
                            <h1 className="font-bold">Confirm</h1>
                            <h3 className="text-sm">Are you sure you want to delete this project?</h3>
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
                        <Button onClick={() => {setShowDeleteProjectModal(false); setProjectToDelete("");}} variant="outlined" color="neutral">
                            Cancel
                        </Button>
                        <Button onClick={() => handleDeleteProject(projectToDelete)} variant="solid" color="danger">
                            Confirm
                        </Button>
                    </div>
                </ModalDialog>
            </Modal>
        </>
    );
};

export default ProjectsIndex;
