import ProjectLayout from "$browser/components/projects/ProjectLayout";
import React from "react";

const Project404: React.FC = () => {
  return (
    <>
      <ProjectLayout>
        <div className="flex h-full flex-row flex-wrap gap-3 border-t-stone-200 p-3">
          <div className="flex h-full w-full flex-col gap-1 p-3">
            <h1 className="text-3xl font-semibold">Oops...</h1>
            <h2 className="text-lg">
              Could not find a page at this address.
            </h2>
          </div>
        </div>
      </ProjectLayout>
    </>
  );
};

export default Project404;