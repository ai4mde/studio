import React from "react";
import ClassConnectionFields from "../ConnectionFields/ClassConnectionFields";

type Props = {
    object: any;
    setObject: (o: any) => void;
};

export const NewActivityConnection: React.FC<Props> = ({
    object,
    setObject,
}) => {
    return <ClassConnectionFields object={object} setObject={setObject} />;
};

export default NewActivityConnection;
