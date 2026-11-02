import { partialUpdateNode } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";
import React, { useEffect, useMemo, useState } from "react";
import { Save } from "lucide-react";
import { Node } from "reactflow";
import style from "./editname.module.css";
import { useClassifiers } from "../../../../../../../../api/metadata/hooks/classifier";
import { classifierNameExists } from "../../../../../../../../api/metadata/classifier";
import type { ClassifierRead } from "../../../../../../../../api/metadata/classifier";

type Props = {
    node: Node;
};

const Button: React.FC<any> = ({ dirty, disabled, title }) => {
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

export const EditName: React.FC<Props> = ({ node }) => {
    const [name, setName] = useState(node.data.name);
    const { diagram, systemId } = useDiagramStore();

    const {
        data: classifiers = [],
        isFetching: checkingName,
        isError: classifierLoadError,
    } = useClassifiers(
        { system_id: systemId || undefined },
        !!systemId,
    );

    const trimmedName = useMemo(() => (name ?? "").trim(), [name]);
    const originalName = useMemo(() => (node.data.name ?? "").trim(), [node.data.name]);
    const dirty = trimmedName !== originalName;

    const ctype = (node.type ?? node.data?.type ?? "").toString();

    // best-effort classifier id for excludeId (depends on how your node payload is shaped)
    const excludeId = useMemo(() => {
        const maybe = (node.data?.id ?? node.data?.cls_ptr ?? "") as any;
        return typeof maybe === "string" ? maybe : "";
    }, [node.data]);

    const nameError =
        dirty &&
        trimmedName &&
        systemId &&
        !classifierLoadError &&
        classifierNameExists(
            classifiers,
            trimmedName,
            ctype as ClassifierRead["type"],
            excludeId || undefined,
        )
            ? `A classifier with the name "${trimmedName}" is already used in this system.`
            : "";

    const handleSubmit: React.FormEventHandler<HTMLFormElement> = (e) => {
        e.preventDefault();

        if (!dirty || !!nameError || checkingName) return;

        partialUpdateNode(diagram, node.id, {
            cls: {
                name: trimmedName,
            },
        });
    };

    const saveDisabled = !!nameError || checkingName || !dirty || !trimmedName;

    const saveTitle =
        nameError
            ? nameError
            : checkingName
            ? "Checking name…"
            : !dirty
            ? "Name is unchanged"
            : !trimmedName
            ? "Name cannot be empty"
            : "";

    return (
        <div className="flex w-full flex-col gap-2 font-mono">
            <span className="w-full border-b border-solid border-gray-400 py-1 font-mono text-xs">
                Name
            </span>
            <form
                className={[
                    style.editname,
                    dirty && style.dirty,
                ]
                    .filter(Boolean)
                    .join(" ")}
                onSubmit={handleSubmit}
            >
                <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                ></input>

                <Button
                    dirty={dirty}
                    disabled={saveDisabled}
                    title={saveTitle}
                />
            </form>

            {/* optional inline hint; remove if you only want hover tooltip */}
            {dirty && nameError && (
                <div className="text-xs text-red-600">
                    {nameError}
                </div>
            )}
        </div>
    );
};

export default EditName;
