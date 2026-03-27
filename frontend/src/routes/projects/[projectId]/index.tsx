import CreateSystem from "$lib/features/browser/components/systems/CreateSystem";
import ListSystem from "$lib/features/browser/components/systems/ListSystem";
import ProjectLayout from "$browser/components/projects/ProjectLayout";
import { GalleryVertical } from "lucide-react";
import React from "react";
import { useParams } from "react-router";
import { useProject } from "$browser/queries";


const ViewProject: React.FC = () => {
  const { projectId } = useParams();
  const project = useProject(projectId);
  const { name, id } = project.data ?? {};

  return (
    <ProjectLayout>
      <CreateSystem project={projectId} />

      <div className="flex h-full flex-row flex-wrap gap-3 border-t-stone-200 p-3">
        <div className="flex w-full flex-col gap-3">
          <span className="flex flex-row items-center gap-2">
            <GalleryVertical size={24} />
            <h1 className="text-lg">
              Systems - {name} ({id?.split("-").slice(-1)})
            </h1>
          </span>

          <div className="flex flex-row flex-nowrap gap-2 rounded-md bg-stone-100 p-2">
            <ListSystem project={projectId} />
          </div>
        </div>
      </div>
    </ProjectLayout>
  );
};

export default ViewProject;