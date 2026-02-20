import React, { useEffect, useMemo, useState } from "react";
import { FormControl, FormLabel, Input, Option, Select } from "@mui/joy";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { authAxios } from "$lib/features/auth/state/auth";
import { useDiagramStore } from "$diagram/stores";
import { useSystemObjectClassifiers } from "$diagram/components/modals/ImportNodeModal/queries/importNode";
import { Save } from "lucide-react";
import style from "../EditName/editname.module.css"; // <-- adjust path to your editname.module.css

type Props = { node: any };

const SaveIconButton: React.FC<{
  dirty: boolean;
  disabled: boolean;
  title?: string;
}> = ({ dirty, disabled, title }) => {
  return (
    <button
      type="submit"
      className={style.save}
      disabled={!dirty || disabled}
      title={title}
    >
      <Save size={12} />
    </button>
  );
};

export const EditObject: React.FC<Props> = ({ node }) => {
  const { diagram, systemId } = useDiagramStore();
  const queryClient = useQueryClient();

  const [objectClassifiers, ok] = useSystemObjectClassifiers(systemId);

  const currentClsId = node.data?.cls ?? null;

  // --- State inline editing ---
  const [state, setState] = useState<string>(node.data?.state ?? "");

  useEffect(() => {
    // reset when node changes
    setState(node.data?.state ?? "");
  }, [node.id]);

  const trimmedState = useMemo(() => (state ?? "").trim(), [state]);
  const originalState = useMemo(
    () => ((node.data?.state ?? "") as string).trim(),
    [node.data?.state],
  );
  const stateDirty = trimmedState !== originalState;

  const clsNameById = useMemo(() => {
    const m = new Map<string, string>();
    for (const c of objectClassifiers ?? []) {
      if (c?.id && c?.data?.name) m.set(String(c.id), c.data.name);
    }
    return m;
  }, [objectClassifiers]);

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

  const saveState: React.FormEventHandler<HTMLFormElement> = (e) => {
    e.preventDefault();
    if (!stateDirty || patch.isPending) return;

    patch.mutate({
      // empty -> null so backend can clear the field
      state: trimmedState ? trimmedState : null,
    });
  };

  return (
    <>
      <FormControl size="sm" className="w-full">
        <FormLabel>Class</FormLabel>
        <Select
          placeholder={!ok ? "Loading..." : "Choose a class..."}
          value={currentClsId}
          onChange={(_, v) => {
            const id = v ? String(v) : null;
            if (!id) return;

            const name = clsNameById.get(id) ?? "";
            // set cls and also update name to match selected class
            patch.mutate({ cls: id, name });
          }}
          disabled={!ok}
          required
        >
          {ok &&
            objectClassifiers.map((c) => (
              <Option key={c.id} value={String(c.id)}>
                {c.data?.name} ({c.data?.type})
              </Option>
            ))}
        </Select>
      </FormControl>

      <div className="flex w-full flex-col gap-2 font-mono">
        <span className="w-full border-b border-solid border-gray-400 py-1 font-mono text-xs">
          State (optional)
        </span>

        <form
          className={[style.editname, stateDirty && style.dirty]
            .filter(Boolean)
            .join(" ")}
          onSubmit={saveState}
        >
          <input
            type="text"
            value={state}
            onChange={(e) => setState(e.target.value)}
            placeholder="e.g. pending, approved..."
          />

          <SaveIconButton
            dirty={stateDirty}
            disabled={patch.isPending}
            title={
              patch.isPending
                ? "Saving…"
                : !stateDirty
                ? "State is unchanged"
                : ""
            }
          />
        </form>
      </div>
    </>
  );
};

export default EditObject;