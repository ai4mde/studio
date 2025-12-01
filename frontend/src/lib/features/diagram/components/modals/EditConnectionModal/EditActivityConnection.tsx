import React from "react";
import ActivityConnectionFields from "../ConnectionFields/ActivityConnectionFields";

type Props = {
    object: any;
    setObject: (o: any) => void;
};

export const EditActivityConnection: React.FC<Props> = ({
    object,
    setObject,
}) => {
    return <ActivityConnectionFields object={object} setObject={setObject} />;
};

export default EditActivityConnection;
