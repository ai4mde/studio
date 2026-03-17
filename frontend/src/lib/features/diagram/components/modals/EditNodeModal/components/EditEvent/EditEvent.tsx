import React, { useMemo } from "react";
import { FormControl, FormLabel, Option, Select } from "@mui/joy";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { authAxios } from "$lib/features/auth/state/auth";
import { useDiagramStore } from "$diagram/stores";
import { useSystemSignalClassifiers } from "$diagram/components/modals/ImportNodeModal/queries/importNode";

type Props = { node: any };

export const EditEvent: React.FC<Props> = ({ node }) => {
  const { diagram, systemId } = useDiagramStore();
  const queryClient = useQueryClient();

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
      await authAxios.patch(`/v1/diagram/${diagram}/node/${node.id}/`, {
        cls: clsPatch,
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["diagram"] });
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
              {s.data?.name} ({s.data?.type})
            </Option>
          ))}
      </Select>
    </FormControl>
  );
};

export default EditEvent;