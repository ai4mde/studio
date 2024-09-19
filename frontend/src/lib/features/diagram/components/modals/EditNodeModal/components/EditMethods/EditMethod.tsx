import Editor from "@monaco-editor/react";
import { X, Pencil, PanelTopClose, Trash2 } from "lucide-react";
import {
    Button,
    FormControl,
    FormLabel,
    Textarea,
} from "@mui/joy";
import React, { useState } from "react";
import Select from "react-select";
import style from "./editmethods.module.css";

const EditMethod: React.FC<{
    method: any;
    update: (v: any) => void;
    del: () => void;
    dirty?: boolean;
    create?: boolean;
}> = ({ method, del, update, dirty, create }) => {
    const [openEditMenu, setOpenEditMenu] = useState(false);
    const [openGenerateModal, setOpenGenerateModal] = useState(false);
    const LLMOptions = [
        { value: 'GPT-4o', label: 'GPT-4o' },
    ]
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
                    <button type="button" onClick={() => {setOpenEditMenu((openEditMenu) => !openEditMenu)}}>
                        { openEditMenu ?
                            <PanelTopClose size={20} />
                            : <Pencil size={20} />
                        }
                    </button>
                    <button type="button" onClick={del}>
                        <Trash2 size={20}/>
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
                        onSubmit={() => {}}
                    >
                        <FormControl required>
                            <FormLabel>Description</FormLabel>
                            <Textarea
                                name="description"
                                placeholder="Describe what the method should do, and how attributes are affected by the method"
                                minRows={4}
                                maxRows={4}
                                required
                            />
                        </FormControl>
                    </form>
                    <div className="flex flex-row gap-4 pt-1">
                        <Button form="generate-method" type="submit" disabled>
                            Generate
                        </Button>
                        <Select
                            options={LLMOptions}
                            value={LLMOptions[0]}
                        />
                        <button type="button" onClick={() => setOpenGenerateModal(false)}>
                            <X size={20}/>
                        </button>
                    </div>
                </div>
            )}
        </>
    );
};

export default EditMethod;
