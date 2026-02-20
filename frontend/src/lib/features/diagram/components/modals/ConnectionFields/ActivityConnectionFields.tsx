import { FormControl, FormLabel, Input } from "@mui/joy";
import React, { useEffect } from "react";

type Props = {
  object: any;
  setObject: (o: any) => void;
};

export const ActivityConnectionFields: React.FC<Props> = ({ object, setObject }) => {
  // force defaults once (no dropdown anywhere)
  useEffect(() => {
    setObject((o: any) => ({
      ...o,
      isDirected: o?.isDirected ?? true,
      type: "controlflow",
    }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <>
      <FormControl size="sm" className="w-full">
        <FormLabel>Guard</FormLabel>
        <Input
          value={object.guard ?? ""}
          onChange={(e) =>
            setObject((o: any) => ({
              ...o,
              guard: e.target.value,
              type: "controlflow",
            }))
          }
        />
      </FormControl>

      <FormControl size="sm" className="w-full">
        <FormLabel>Weight</FormLabel>
        <Input
          value={object.weight ?? ""}
          onChange={(e) =>
            setObject((o: any) => ({
              ...o,
              weight: e.target.value,
              type: "controlflow",
            }))
          }
        />
      </FormControl>
    </>
  );
};

export default ActivityConnectionFields;