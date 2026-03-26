import { useProject } from "$browser/queries";
import { TopNavigation } from "$shared/components/TopNavigation";
import React from "react";
import { useParams } from "react-router";
import { GalleryVertical, User, Rocket } from "lucide-react";
import LinearProgress from "@mui/joy/LinearProgress/LinearProgress";

type Props = {
    children?: React.ReactNode;
}

const ProjectLayout: React.FC<Props> = ({ children }) => {
    const { projectId } = useParams();
    const project = useProject(projectId);

    return (
        <div
            className="grid h-full w-full grid-cols-12 items-center"
            style={{
                gridTemplateRows: "fit-content(4rem) 1fr fit-content(4rem)",
            }}
        >
            <div className="col-span-12">
                <TopNavigation
                    back={"/projects/"}
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
                        {
                            name: "Versions",
                            Icon: Rocket,
                            href: `/projects/${projectId}/versions`,
                            strict: true,
                        }
                    ]}
                />
            </div>

            <div className="col-span-12 h-full">
                {!projectId ? (
                <div className="flex h-full items-center justify-center">
                    <h1 className="text-lg">Invalid project</h1>
                </div>
                ) : project.isLoading ? (
                <div className="flex h-full items-center justify-center">
                    <LinearProgress className="w-full" />
                </div>
                ) : (
                children
                )}
            </div>
            <div className="col-span-12 flex flex-row">AI4MDE</div>
        </div>
    )
}

export default ProjectLayout;