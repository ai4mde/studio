import React, { useEffect } from "react";
import ActivityConnectionFields from "../ConnectionFields/ActivityConnectionFields";

type Props = {
    object: any;
    setObject: (o: any) => void;
};

export const NewActivityConnection: React.FC<Props> = ({
    object,
    setObject,
}) => {
    // Set some defaults on the edge
    useEffect(
        () =>
            setObject((o: any) => ({
                isDirected: true,
                type: "controlflow",
                ...o,
            })),
        [],
    );

    return <ActivityConnectionFields object={object} setObject={setObject} />;
};

export default NewActivityConnection;
