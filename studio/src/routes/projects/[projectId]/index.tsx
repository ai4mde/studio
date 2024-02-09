import { authAxios } from "$lib/features/auth/state/auth";
import CreateSystem from "$lib/features/browser/components/systems/CreateSystem";
import ListSystem from "$lib/features/browser/components/systems/ListSystem";
import { TopNavigation } from "$lib/shared/components/TopNavigation";
import { LinearProgress } from "@mui/joy";
import { useQuery } from "@tanstack/react-query";
import { GalleryVertical, User } from "lucide-react";
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

    if (!projectId) {
        return <> </>;
    }

    if (project.isLoading) {
        return (
            <>
                <LinearProgress className="absolute left-0 right-0 top-0" />
            </>
        );
    }

    return (
        <>
            <CreateSystem project={projectId} />
            <div
                className="grid h-full w-full grid-cols-12 items-center"
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
                                href: `/projects/${projectId}`,
                                strict: true,
                            },
                            {
                                name: "Users",
                                Icon: User,
                                href: `/projects/${projectId}/users`,
                            },
                        ]}
                    />
                </div>

                <div className="col-span-12 flex h-full flex-row flex-wrap gap-3 border-t-stone-200 p-3">
                    {project.isLoading && (
                        <LinearProgress className="absolute left-0 right-0 top-0" />
                    )}

                    <div className="flex w-full flex-col gap-3">
                        <span className="flex flex-row items-center gap-2">
                            <GalleryVertical size={24} />
                            <h1 className="text-lg">
                                Systems - {name} ({id?.split("-").slice(-1)})
                            </h1>
                        </span>
                        <div className="flex flex-row flex-nowrap gap-2 rounded-md bg-stone-100 p-2 ">
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
