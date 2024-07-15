import React, { useState, useEffect } from "react";
import { Package } from "lucide-react";

type Props = {
    systemId: string;
};

export const ShowPrototypes: React.FC<Props> = ({ systemId }) => {

    return (
        <>
            <span className="flex flex-row items-center gap-2">
                <Package size={24} />
                <h1 className="text-lg">Prototypes</h1>
            </span>
        </>
    );
};

export default ShowPrototypes;
