import React from "react";

export const NotFoundPage: React.FC = () => {
    return (
        <>
            <div className="flex flex-col gap-4 p-4">
                <h1 className="text-xl">Oops...</h1>
                <h4 className="text-lg">Could not find this page.</h4>
            </div>
        </>
    );
};

export default NotFoundPage;
