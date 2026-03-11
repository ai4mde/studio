import { partialUpdateNode } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";
import { Button } from "@mui/joy";
import { isEqualWith } from "lodash";
import React, { useMemo, useState } from "react";
import { Node } from "reactflow";
import EditInternal from "./EditInternal";
import style from "../EditAttributes/editattributes.module.css";

type Props = {
  node: Node;
};

const EditInternals: React.FC<Props> = ({ node }) => {
  const [internals, setInternals] = useState(node?.data?.internals ?? []);
  const { diagram } = useDiagramStore();

  const dirty = useMemo(
    () => !isEqualWith(internals, node?.data?.internals),
    [internals, node?.data?.internals],
  );

  return (
    <div className={style.attributes}>
      <span className="w-full border-b border-solid border-gray-400 py-1 text-xs">
        Internals
      </span>

      {internals.map((e: any, idx: number) => (
        <EditInternal
          key={`internal-${idx}`}
          internal={e}
          update={(v) => {
            setInternals((s: any[]) => {
              s[idx] = v;
              return [...s];
            });
          }}
          del={() => {
            setInternals((s: any[]) => s.filter((_, i) => i !== idx));
          }}
        />
      ))}

      <div className="flex flex-row items-center justify-stretch gap-2">
        <Button
          color="success"
          className="w-full"
          size="sm"
          variant="outlined"
          onClick={() =>
            setInternals((s: any[]) => [
              ...s,
              {
                name: "",
                type: null,
                typeName: null,
              },
            ])
          }
        >
          Add Internal
        </Button>

        <Button
          disabled={!dirty}
          color="primary"
          className="w-full"
          size="sm"
          onClick={() =>
            partialUpdateNode(diagram, node.id, {
              cls: {
                internals,
              },
            })
          }
        >
          Save
        </Button>
      </div>
    </div>
  );
};

export default EditInternals;