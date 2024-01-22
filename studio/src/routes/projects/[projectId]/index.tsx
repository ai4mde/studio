import { createProjectAtom } from "$browser/atoms";
import { CreateProject } from "$browser/components/projects/CreateProject";
import { authAxios } from "$lib/features/auth/state/auth";
import ListSystem from "$lib/features/browser/components/systems/ListSystem";
import { Button, ButtonGroup, LinearProgress } from "@mui/joy";
import { useAtom } from "jotai";
import { ArrowLeft } from "lucide-react";
import React from "react";
import { useQuery } from "react-query";
import { useParams } from "react-router";

type ProjectOut = {
    id: string;
    name: string;
    description?: string;
};

const ViewProject: React.FC = () => {
    const [, setCreate] = useAtom(createProjectAtom);
    const { projectId } = useParams();

    const project = useQuery<ProjectOut>({
        queryKey: ["project", `${projectId}`],
        queryFn: async () => {
            return (await authAxios.get(`/v1/metadata/projects/${projectId}`))
                .data;
        },
        enabled: !!projectId,
    });

    const { name, description } = project.data ?? {};

    if (project.isLoading) {
        return (
            <>
                <LinearProgress className="absolute top-0 left-0 right-0" />
            </>
        );
    }

    return (
        <>
            <CreateProject />
            <div
                className="w-full h-full grid grid-cols-12 gap-2 p-4 items-center"
                style={{
                    gridTemplateRows: "fit-content(4rem) 1fr fit-content(4rem)",
                }}
            >
                <div className="col-span-6 flex flex-row gap-3 items-center">
                    <a href="/projects">
                        <ArrowLeft />
                    </a>
                    <div className="flex flex-col">
                        <h1 className="text-xl">{name ?? "-"}</h1>
                        <h3 className="text-sm">{description ?? "-"}</h3>
                    </div>
                </div>
                <div className="col-span-6 flex flex-row justify-end h-fit">
                    <ButtonGroup>
                        <Button onClick={() => setCreate(true)}>
                            New System
                        </Button>
                    </ButtonGroup>
                </div>
                <div className="col-span-12 pt-4 mt-2 border-t border-t-stone-200 flex flex-col gap-4 h-full">
                    {projectId && <ListSystem project={projectId} />}
                </div>
                <div className="col-span-12 flex flex-row">AI4MDE</div>
            </div>
        </>
    );
};

export default ViewProject;
