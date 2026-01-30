import { partialUpdateNode } from "$diagram/mutations/diagram";
import { useDiagramStore } from "$diagram/stores";
import React, { useEffect, useMemo, useState } from "react";
import { Save } from "lucide-react";
import { Node } from "reactflow";
import style from "./editname.module.css";
import { authAxios } from "$lib/features/auth/state/auth";

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

    const [nameError, setNameError] = useState("");
    const [checkingName, setCheckingName] = useState(false);
    const [lastCheckedName, setLastCheckedName] = useState("");

    const trimmedName = useMemo(() => (name ?? "").trim(), [name]);
    const originalName = useMemo(() => (node.data.name ?? "").trim(), [node.data.name]);
    const dirty = trimmedName !== originalName;

    const ctype = (node.type ?? node.data?.type ?? "").toString();

    // best-effort classifier id for excludeId (depends on how your node payload is shaped)
    const excludeId = useMemo(() => {
        const maybe = (node.data?.id ?? node.data?.cls_ptr ?? "") as any;
        return typeof maybe === "string" ? maybe : "";
    }, [node.data]);

    useEffect(() => {
        setNameError("");
        setCheckingName(false);
        setLastCheckedName("");
        setName(node.data.name);
    }, [node.id]);

    useEffect(() => {
        // you said it's fine to disable when unchanged
        if (!dirty) {
            setNameError("");
            setCheckingName(false);
            setLastCheckedName("");
            return;
        }

        if (!trimmedName) {
            setNameError("");
            setCheckingName(false);
            setLastCheckedName("");
            return;
        }

        if (!systemId) {
            setNameError("");
            setCheckingName(false);
            return;
        }

        if (trimmedName === lastCheckedName) return;

        let cancelled = false;
        setCheckingName(true);

        const t = window.setTimeout(async () => {
            try {
                const res = await authAxios.get(
                    `/v1/metadata/systems/${systemId}/classifiers/exists/`,
                    {
                        params: {
                            name: trimmedName,
                            ctype,
                            excludeId: excludeId || undefined,
                        },
                    },
                );

                if (cancelled) return;

                setLastCheckedName(trimmedName);

                if (res.data?.exists) {
                    setNameError(`A classifier with the name "${trimmedName}" is already used in this system.`);
                } else {
                    setNameError("");
                }
            } catch {
                if (!cancelled) setNameError(""); // fail open
            } finally {
                if (!cancelled) setCheckingName(false);
            }
        }, 250);

        return () => {
            cancelled = true;
            window.clearTimeout(t);
        };
    }, [dirty, trimmedName, systemId, ctype, excludeId, lastCheckedName]);

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
