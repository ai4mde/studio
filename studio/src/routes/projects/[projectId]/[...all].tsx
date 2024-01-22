import { authAxios } from "$lib/features/auth/state/auth";
import CreateSystem from "$lib/features/browser/components/systems/CreateSystem";
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

const Project404: React.FC = () => {
    const { projectId } = useParams();

    const project = useQuery<ProjectOut>({
        queryKey: ["project", `${projectId}`],
        queryFn: async () => {
            return (await authAxios.get(`/v1/metadata/projects/${projectId}`))
                .data;
        },
        enabled: !!projectId,
    });

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

                <div className="col-span-12 border-t-stone-200 flex flex-row p-3 gap-3 flex-wrap h-full">
                    <div className="flex flex-col p-3 gap-1 h-full w-full">
                        <h1 className="text-3xl font-semibold">Oops...</h1>
                        <h2 className="text-lg">
                            Could not find a page at this address.
                        </h2>
                    </div>
                </div>
                <div className="col-span-12 flex flex-row">AI4MDE</div>
            </div>
        </>
    );
};

export default Project404;
