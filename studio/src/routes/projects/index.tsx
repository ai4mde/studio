import { createProjectAtom } from "$browser/atoms";
import { CreateProject } from "$browser/components/projects/CreateProject";
import { Button, ButtonGroup } from "@mui/joy";
import { useAtom } from "jotai";
import React from "react";

const ProjectsIndex: React.FC = () => {
    const [, setCreate] = useAtom(createProjectAtom);

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
                <div className="col-span-12 flex flex-row flex-wrap h-full"></div>
                <div className="col-span-12 flex flex-row">Footer</div>
            </div>
        </>
    );
};

export default ProjectsIndex;
