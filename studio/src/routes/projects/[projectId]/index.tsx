import { authAxios } from "$lib/features/auth/state/auth";
import CreateSystem from "$lib/features/browser/components/systems/CreateSystem";
import ListSystem from "$lib/features/browser/components/systems/ListSystem";
import { TopNavigation } from "$lib/shared/components/TopNavigation";
import { LinearProgress } from "@mui/joy";
import { useQuery } from "@tanstack/react-query";
import { GalleryVertical } from "lucide-react";
import React from "react";
import { useParams } from "react-router";

type ProjectOut = {
    id: string;
    name: string;
    description?: string;
};

const ViewProject: React.FC = () => {
    const { projectId } = useParams();

    const project = useQuery<ProjectOut>({
        queryKey: ["project", `${projectId}`],
        queryFn: async () => {
            return (await authAxios.get(`/v1/metadata/projects/${projectId}`))
                .data;
        },
        enabled: !!projectId,
    });

    const { name, id } = project.data ?? {};

    if (project.isLoading) {
        return (
            <>
                <LinearProgress className="absolute top-0 left-0 right-0" />
            </>
        );
    }

    return (
        <>
            {projectId && <CreateSystem project={projectId} />}
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
                                name: "Systems",
                                Icon: GalleryVertical,
                                href: "/systems",
                            },
                        ]}
                    />
                </div>

                <div className="col-span-12 border-t-stone-200 flex flex-row p-3 gap-3 flex-wrap h-full">
                    {project.isLoading && (
                        <LinearProgress className="absolute top-0 left-0 right-0" />
                    )}

                    <div className="flex flex-col gap-3 w-full">
                        <span className="flex flex-row gap-2 items-center">
                            <GalleryVertical size={24} />
                            <h1 className="text-lg">
                                Systems - {name} ({id?.split("-").slice(-1)})
                            </h1>
                        </span>
                        <div className="flex flex-row flex-nowrap rounded-md bg-stone-100 p-2 gap-2 ">
                            {projectId && <ListSystem project={projectId} />}
                        </div>
                    </div>
                </div>
                <div className="col-span-12 flex flex-row">AI4MDE</div>
            </div>
        </>
    );
};

export default ViewProject;
