import { useDiagramStore } from "$diagram/stores";
import { X } from "lucide-react";
import React from "react";
import Select from "react-select";
import { useSystemInternalTypeClassifiers } from "$diagram/components/modals/ImportNodeModal/queries/importNode";
import style from "$diagram/components/modals/EditNodeModal/components/EditAttributes/editattributes.module.css";

const EditInternal: React.FC<{
  internal: any;
  update: (v: any) => void;
  del: () => void;
}> = ({ internal, update, del }) => {
  const systemId = useDiagramStore((s) => s.systemId);
  const [classifiers, isSuccess] = useSystemInternalTypeClassifiers(systemId);

  const selectOptions = (classifiers ?? []).map((c) => ({
    value: c.id,
    label: `${c.data?.name} (${c.data?.type})`,
  }));

  return (
    <div className="bg-stone-100">
      <div className={style.attribute}>
        <input
          type="text"
          value={internal?.name ?? ""}
          placeholder="Internal name"
          onChange={(e) =>
            update({
              ...internal,
              name: e.target.value,
            })
          }
        />

        <span className="p-2">:</span>

        <Select
          value={
            selectOptions.find((option) => option.value === internal?.type) ?? null
          }
          options={selectOptions}
          onChange={(selectedOption) =>
            update({
              ...internal,
              type: selectedOption?.value ?? null,
              typeName: selectedOption?.label ?? null,
            })
          }
          className="w-80"
          isDisabled={!isSuccess}
        />

        <button type="button" onClick={del} className={style.delete}>
          <X size={12} />
        </button>
      </div>
    </div>
  );
};

export default EditInternal;