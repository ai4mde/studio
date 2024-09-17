import Editor from "@monaco-editor/react";
import { X } from "lucide-react";
import {
    Button,
    Divider,
    FormControl,
    FormLabel,
    Input,
    Modal,
    ModalClose,
    ModalDialog,
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
    const [openGenerateModal, setOpenGenerateModal] = useState(false);
    const LLMOptions = [
        { value: 'GPT-4o', label: 'GPT-4o' },
    ]
    return (
        <>
            <div
                className={[style.method, create && style.new, dirty && style.dirty]
                    .filter(Boolean)
                    .join(" ")}
            >
                <div className={style.header}>
                    <span className="p-2">+</span>
                    <input
                        type="text"
                        value={method?.name}
                        onChange={(e) =>
                            update({ ...method, name: e.target.value })
                        }
                    ></input>
                    <span className="p-2">:</span>
                    <select
                        value={method?.type}
                        onChange={(e) =>
                            update({ ...method, type: e.target.value })
                        }
                    >
                        <option value="str">string</option>
                        <option value="int">integer</option>
                        <option value="bool">boolean</option>
                    </select>
                    <button type="button" onClick={del} className={style.delete}>
                        <X size={12} />
                    </button>
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
            </div>

            <Button
                color="primary"
                className="w-full"
                size="sm"
                variant="outlined"
                onClick={() => setOpenGenerateModal(true)}
            >
                Generate using LLM
            </Button>
            <Modal open={openGenerateModal} onClose={() => setOpenGenerateModal(false)}>
                <ModalDialog>
                    <div className="flex w-full flex-row justify-between pb-1">
                        <div className="flex flex-col">
                            <h1 className="font-bold">Generate a Custom Method using an LLM</h1>
                        </div>
                        <ModalClose
                            sx={{
                                position: "relative",
                                top: 0,
                                right: 0,
                            }}
                        />
                    </div>
                    <form
                        id="generate-method"
                        className="flex min-w-96 flex-col gap-2"
                        onSubmit={() => {}}
                    >
                        <FormControl required>
                            <FormLabel>Name</FormLabel>
                            <Input name="name" placeholder="Method name" required />
                        </FormControl>
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
                    <Divider />
                    <div className="flex flex-row gap-4 pt-1">
                        <Button form="generate-method" type="submit" disabled>
                            Generate
                        </Button>
                        <Select
                            options={LLMOptions}
                            value={LLMOptions[0]}
                        />
                    </div>
                </ModalDialog>
            </Modal>
        </>
    );
};

export default EditMethod;
