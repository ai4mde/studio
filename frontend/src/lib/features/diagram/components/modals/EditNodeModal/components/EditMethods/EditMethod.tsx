import { useDiagramStore } from "$diagram/stores";
import { authAxios } from "$lib/features/auth/state/auth";
import Editor from "@monaco-editor/react";
import {
    Button,
    FormControl,
    FormLabel,
    Textarea,
} from "@mui/joy";
import { PanelTopClose, Pencil, Trash2, X } from "lucide-react";
import React, { useState } from "react";
import Select from "react-select";
import style from "./editmethods.module.css";

const EditMethod: React.FC<{
    method: any;
    node: any;
    update: (v: any) => void;
    del: () => void;
    dirty?: boolean;
    create?: boolean;
}> = ({ method, node, del, update, dirty, create }) => {
    const [openEditMenu, setOpenEditMenu] = useState(false);
    const [openGenerateModal, setOpenGenerateModal] = useState(false);
    const { diagram } = useDiagramStore();
    const [generationError, setGenerationError] = useState<string | null>(null);
    const LLMOptions = [
        { value: 'mixtral-8x7b-32768', label: 'mixtral-8x7b-32768' },
        { value: 'llama-3.3-70b-versatile', label: 'llama-3.3-70b-versatile' },
        { value: 'gpt-4o', label: 'gpt-4o' },
    ]
    const [generateButtonDisabled, setGenerateButtonDisabled] = useState(false);
    const [selectedLLMOption, setSelectedLLMOption] = useState(LLMOptions[0]);

    const generateMethod = async (event) => {
        event.preventDefault();
        setGenerationError(null);
        setGenerateButtonDisabled(true)
        try {
            const { data } = await authAxios.post(`v1/diagram/${diagram}/node/${node.id}/generate_method/?name=${method.name}&description=${method.description}&model=${selectedLLMOption.value}`);
            update({ ...method, body: data })
            setOpenGenerateModal(false);
        } catch (error) {
            setGenerationError("Failed to generate method: API call failed.");
        } finally {
            setGenerateButtonDisabled(false)
        }
    }

    return (
        <>
            <div className={style.header}>
                <div className="flex flex-row gap-1 items-center h-full">
                    <span className="p-2">+</span>
                    <input
                        type="text"
                        value={method?.name}
                        onChange={(e) =>
                            update({ ...method, name: e.target.value })
                        }
                        placeholder="Enter method name..."
                    ></input>
                    <button type="button" onClick={() => { setOpenEditMenu((openEditMenu) => !openEditMenu) }}>
                        {openEditMenu ?
                            <PanelTopClose size={20} />
                            : <Pencil size={20} />
                        }
                    </button>
                    <button type="button" onClick={del}>
                        <Trash2 size={20} />
                    </button>
                </div>
            </div>
            {openEditMenu &&
                <div
                    className={[style.method, create && style.new, dirty && style.dirty]
                        .filter(Boolean)
                        .join(" ")}
                >
                    <div className={style.header}>
                        <select
                            value={method?.type}
                            onChange={(e) =>
                                update({ ...method, type: e.target.value })
                            }
                            className="h-[30px] hover:cursor-pointer"
                        >
                            <option value="str">string</option>
                            <option value="int">integer</option>
                            <option value="bool">boolean</option>
                        </select>
                    </div>
                    <div className={style.body}>
                        <Editor
                            value={method?.body}
                            language="python"
                            options={{
                                lineNumbers: "off",
                                folding: false,
                            }}
                            height="12rem"
                            width="100%"
                            onChange={(e) => update({ ...method, body: e ?? "" })}
                        />
                    </div>
                    {!openGenerateModal &&
                        <Button
                            color="primary"
                            className="w-full"
                            size="sm"
                            variant="outlined"
                            onClick={() => setOpenGenerateModal(true)}
                        >
                            Generate using LLM
                        </Button>
                    }
                </div>
            }
            {openGenerateModal && openEditMenu && (
                <div>
                    <form
                        id="generate-method"
                        className="flex min-w-96 flex-col gap-2"
                        onSubmit={generateMethod}
                    >
                        <FormControl required>
                            <FormLabel>Description</FormLabel>
                            <Textarea
                                name="description"
                                placeholder="Describe what the method should do, and how attributes are affected by the method"
                                minRows={4}
                                maxRows={4}
                                required
                                value={method?.description}
                                onChange={(e) =>
                                    update({ ...method, description: e.target.value })
                                }
                            />
                        </FormControl>
                    </form>
                    <div className="flex flex-row gap-4 pt-1">
                        <Button form="generate-method" type="submit" disabled={!method?.description || generateButtonDisabled}>
                            Generate
                        </Button>
                        <Select
                            options={LLMOptions}
                            value={selectedLLMOption}
                            onChange={setSelectedLLMOption}
                        />
                        <button type="button" onClick={() => { setOpenGenerateModal(false); setGenerationError(null); }}>
                            <X size={20} />
                        </button>
                    </div>
                    {generationError && <p style={{ color: 'red' }}>{generationError}</p>}
                </div>
            )}
        </>
    );
};

export default EditMethod;
