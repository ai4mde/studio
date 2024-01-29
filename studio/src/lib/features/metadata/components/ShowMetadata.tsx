import { useSystemMetadata } from "$metadata/queries";
import { CircularProgress } from "@mui/joy";
import React from "react";

type ShowMetadata = {
    systemId: string;
};

export const ShowMetadata: React.FC<ShowMetadata> = ({ systemId }) => {
    const { data, isSuccess } = useSystemMetadata(systemId);

    if (!isSuccess) {
        return <CircularProgress />;
    }

    return <pre>{JSON.stringify(data, null, 2)}</pre>;
};
