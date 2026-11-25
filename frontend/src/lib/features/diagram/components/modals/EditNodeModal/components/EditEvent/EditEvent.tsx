import React, { useMemo } from "react";
import { FormControl, FormLabel, Option, Select } from "@mui/joy";
import { useMutation } from "@tanstack/react-query";
import { partialUpdateNode } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";
import { useSystemSignalClassifiers } from "$diagram/components/modals/ImportNodeModal/queries/importNode";

type Props = { node: any };

export const EditEvent: React.FC<Props> = ({ node }) => {
  const { diagram, systemId } = useDiagramStore();

  const [signalClassifiers, ok] = useSystemSignalClassifiers(systemId);

  const signalNameById = useMemo(() => {
    const m = new Map<string, string>();
    for (const s of signalClassifiers ?? []) {
      if (s?.id && s?.data?.name) m.set(String(s.id), s.data.name);
    }
    return m;
  }, [signalClassifiers]);

  const patch = useMutation({
    mutationFn: async (clsPatch: Record<string, any>) => {
      await partialUpdateNode(diagram, node.id, {
        cls: clsPatch,
      });
    },
  });

  return (
    <FormControl size="sm" className="w-full">
      <FormLabel>Signal</FormLabel>
      <Select
        placeholder={!ok ? "Loading..." : "Choose a signal..."}
        value={node.data?.signal ?? null}
        onChange={(_, v) => {
          const id = v ? String(v) : null;
          if (!id) return;

          const name = signalNameById.get(id) ?? "";
          // set signal and also update name to match selected signal
          patch.mutate({ signal: id, name });
        }}
        disabled={!ok}
        required
      >
        {ok &&
          signalClassifiers.map((s) => (
            <Option key={s.id} value={String(s.id)}>
              {s.data?.name} ({s.type})
            </Option>
          ))}
      </Select>
    </FormControl>
  );
};

export default EditEvent;