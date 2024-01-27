import { FormControl, FormLabel, Input } from "@mui/joy";
import React, { useEffect } from "react";

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
                type: "activity",
                ...o,
            })),
        []
    );

    return (
        <>
            <FormControl size="sm" className="w-full">
                <FormLabel>Guard</FormLabel>
                <Input
                    value={object.guard}
                    onChange={(e) =>
                        setObject((o: any) => ({
                            ...o,
                            guard: e.target.value,
                        }))
                    }
                ></Input>
            </FormControl>
            <FormControl size="sm" className="w-full">
                <FormLabel>Weight</FormLabel>
                <Input
                    value={object.weight}
                    onChange={(e) =>
                        setObject((o: any) => ({
                            ...o,
                            weight: e.target.value,
                        }))
                    }
                ></Input>
            </FormControl>
        </>
    );
};

export default NewActivityConnection;
