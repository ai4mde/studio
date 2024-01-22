import { createProjectAtom } from "$browser/atoms";
import { CreateProject } from "$browser/components/projects/CreateProject";
import { authAxios } from "$lib/features/auth/state/auth";
import { TopNavigation } from "$lib/shared/components/TopNavigation";
import { LinearProgress } from "@mui/joy";
import { useQuery } from "@tanstack/react-query";
import { useAtom } from "jotai";
import { Box, Plus } from "lucide-react";
import React from "react";

type ProjectOut = {
    id: string;
    name: string;
    description?: string;
};

const ProjectsIndex: React.FC = () => {
    const [, setCreate] = useAtom(createProjectAtom);

    const { isLoading, isSuccess, data } = useQuery<ProjectOut[]>({
        queryKey: ["projects"],
        queryFn: async () => {
            return (await authAxios.get("/v1/metadata/projects/")).data;
        },
    });

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
                                ))}
                            <button
                                onClick={() => setCreate(true)}
                                className="flex flex-col gap-2 p-4 rounded-md bg-stone-100 hover:bg-stone-200 h-fill items-center"
                            >
                                <Plus />
                            </button>
                        </div>
                    </div>
                </div>
                <div className="col-span-12 flex flex-row">AI4MDE</div>
            </div>
        </>
    );
};

export default ProjectsIndex;
