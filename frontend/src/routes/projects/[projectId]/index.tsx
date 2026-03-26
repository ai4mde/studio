import { authAxios } from "$lib/features/auth/state/auth";
import CreateSystem from "$lib/features/browser/components/systems/CreateSystem";
import ListSystem from "$lib/features/browser/components/systems/ListSystem";
import ProjectLayout from "$browser/components/projects/ProjectLayout";
import { LinearProgress } from "@mui/joy";
import { GalleryVertical, Download } from "lucide-react";
import React from "react";
import { useParams } from "react-router";
import { useProject } from "$browser/queries";


const ViewProject: React.FC = () => {
  const { projectId } = useParams();
  const project = useProject(projectId);
  const { name, id } = project.data ?? {};

  const handleExportProject = async () => {
    const response = await authAxios.get(`/v1/metadata/projects/export/${projectId}/`);
    const jsonStr = JSON.stringify(response.data, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = `${project.data?.name ?? "project"}.json`;

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

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

          <button
            className="flex w-full items-center justify-center gap-1 rounded-md bg-stone-100 p-4 hover:bg-stone-200"
            onClick={handleExportProject}
          >
            <Download size={16} />
            <h2 className="text-base">Export Project</h2>
          </button>
        </div>
      </div>
    </ProjectLayout>
  );
};

export default ViewProject;