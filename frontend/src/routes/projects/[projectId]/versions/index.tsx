import React from "react";
import ProjectLayout from "$browser/components/projects/ProjectLayout";
import ShowReleases from "lib/features/releases/components/ShowReleases";
import { useProject } from "$browser/queries";
import { useParams } from "react-router";

const ProjectReleases: React.FC = () => {
  const { projectId } = useParams();
  const project = useProject(projectId);
  const { id } = project.data ?? {};

  return (
    <ProjectLayout>
      <div className="flex h-full w-full flex-col gap-1 p-3">
        <ShowReleases project={id} />
      </div>
    </ProjectLayout>
  )

};

export default ProjectReleases;