import SystemLayout from "$lib/features/browser/components/systems/SystemLayout";
import React from "react";

const System404: React.FC = () => {
    return (
        <SystemLayout>
            <div className="flex flex-col p-3 gap-1 h-full w-full">
                <h1 className="text-3xl font-semibold">Oops...</h1>
                <h2 className="text-lg">
                    Could not find a page at this address.
                </h2>
            </div>
        </SystemLayout>
    );
};

export default System404;
