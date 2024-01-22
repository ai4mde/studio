import { createProjectAtom } from "$browser/atoms";
import { CreateProject } from "$browser/components/projects/CreateProject";
import { authAxios } from "$lib/features/auth/state/auth";
import { Button, ButtonGroup, LinearProgress } from "@mui/joy";
import { useAtom } from "jotai";
import { Plus } from "lucide-react";
import React from "react";
import { useQuery } from "react-query";

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
                className="w-full h-full grid grid-cols-12 gap-2 p-4 items-center"
                style={{
                    gridTemplateRows: "fit-content(4rem) 1fr fit-content(4rem)",
                }}
            >
                <div className="col-span-6 flex flex-col">
                    <h1 className="text-xl">Projects</h1>
                    <h3 className="text-sm">
                        Select a project or create a new one
                    </h3>
                </div>
                <div className="col-span-6 flex flex-row justify-end h-fit">
                    <ButtonGroup>
                        <Button onClick={() => setCreate(true)}>
                            New Project
                        </Button>
                    </ButtonGroup>
                </div>
                <div className="col-span-12 pt-4 mt-2 border-t border-t-stone-200 flex flex-row gap-4 flex-wrap h-full">
                    {isLoading && (
                        <LinearProgress className="absolute top-0 left-0 right-0" />
                    )}
                    {isSuccess &&
                        data.map((e) => (
                            <a
                                href={`/projects/${e.id}`}
                                className="flex flex-col gap-2 p-4 rounded-md bg-stone-100 hover:bg-stone-200 h-fit"
                            >
                                <div className="flex flex-col mb-1 pb-2 border-b border-b-stone-400 w-64">
                                    <h3 className="text-lg">{e.name}</h3>
                                    <h4 className="text-sm text-ellipsis text-nowrap overflow-hidden">
                                        {e.description}
                                    </h4>
                                </div>
                                <span className="text-xs">
                                    {e.id.split("-").slice(-1)}
                                </span>
                            </a>
                        ))}
                    <button
                        onClick={() => setCreate(true)}
                        className="flex flex-col gap-2 p-4 rounded-md bg-stone-100 hover:bg-stone-200 h-fit"
                    >
                        <Plus />
                    </button>
                </div>
                <div className="col-span-12 flex flex-row">AI4MDE</div>
            </div>
        </>
    );
};

export default ProjectsIndex;
