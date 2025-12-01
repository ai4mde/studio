import { FormControl, FormLabel, Option, Select } from "@mui/joy";
import React from "react";
import UseCaseConnectionFields from "../ConnectionFields/UseCaseConnectionFields";

type Props = {
    object: any;
    setObject: (o: any) => void;
};

export const NewUsecaseConnection: React.FC<Props> = ({
    object,
    setObject,
}) => {
    // TODO: Use the sourceNode & targetNode to display names
    // or other identifying attribute
    //
    // const sourceNode = useMemo(
    //     () => nodes.find((e) => e.id === source),
    //     [nodes]
    // )
    //
    // const targetNode = useMemo(
    //     () => nodes.find((e) => e.id === target),
    //     [nodes]
    // )
    // interaction
    // extension
    // inclusion
    return <UseCaseConnectionFields object={object} setObject={setObject} />;
};

export default NewUsecaseConnection;
