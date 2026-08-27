import { useDiagramStore } from "$diagram/stores";
import { authAxios } from "$lib/features/auth/state/auth";
import Editor from "@monaco-editor/react";
import { Button, FormControl, FormLabel, Textarea, Tooltip } from "@mui/joy";
import { PanelTopClose, Pencil, X } from "lucide-react";
import React, { useEffect, useState } from "react";
import Select from "react-select";
import { Node } from "reactflow";
import AiConfigSection from "./AiConfigSection";
import style from "./editattributes.module.css";

const EditAttribute: React.FC<{
    attribute: any;
    update: (v: any) => void;
    del: () => void;
    dirty?: boolean;
    create?: boolean;
    node: Node;
}> = ({ attribute, del, update, dirty, create, node }) => {
    const [enumClassifiers, setEnumClassifiers] = useState([]);
    const { diagram } = useDiagramStore();
    const [openEditMenu, setOpenEditMenu] = useState(false);
    const [openGenerateModal, setOpenGenerateModal] = useState(false);
    const [generationError, setGenerationError] = useState<string | null>(null);
    // An attribute is either a plain field, a derived @property, or AI-managed.
    // models.py.jinja2 renders `derived and body` as a read-only @property, which
    // would shadow the database column that ai_config.output.write_back needs to
    // write into. The two are therefore mutually exclusive, enforced in both
    // directions (see also AiConfigSection.tsx).
    const aiManaged = Boolean(attribute?.ai_config);
    const LLMOptions = [
        { value: 'openai/gpt-oss-20b', label: 'gpt-oss-20b (Groq)' },
        { value: 'gpt-5.1', label: 'gpt-5.1 (OpenAI)' },
    ]
    const [generateButtonDisabled, setGenerateButtonDisabled] = useState(false);
    const [selectedLLMOption, setSelectedLLMOption] = useState(LLMOptions[0]);


    useEffect(() => {
        const fetchEnumClassifiers = async () => {
            try {
                const response = await authAxios.get(`/v1/diagram/${diagram}/node/${node.id}/enums/`);
                setEnumClassifiers(response.data);
            } catch (error) {
                console.error("Error fetching enum nodes:", error);
            }
        };

        fetchEnumClassifiers();
    }, []);

    const staticOptions = [
        { value: 'str', label: 'string', id: 'string' },
        { value: 'int', label: 'integer', id: 'integer' },
        { value: 'bool', label: 'boolean', id: 'boolean' },
    ];

    const dynamicOptions = enumClassifiers.map((e) => ({
        value: 'enum',
        label: `enum: ${e.cls.name}`,
        id: e.cls_ptr,
    }));

    const selectOptions = [...staticOptions, ...dynamicOptions];

    const [selectedOption, setSelectedOption] = useState(null);
    const handleSelectChange = (selectedOption) => {
        console.log('Selected value:', selectedOption.value); // Access the value
        setSelectedOption(selectedOption);
        if (selectedOption.value === "enum") {
            let updatedAttribute = {
                ...attribute,
                type: 'enum',
                enum: selectedOption.id
            };
            update(updatedAttribute);
        }
        else {
            let updatedAttribute = {
                ...attribute,
                type: selectedOption.value,
                enum: null
            };
            update(updatedAttribute);
        }
    }

    const generateAttribute = async (event) => {
        event.preventDefault();
        setGenerationError(null);
        setGenerateButtonDisabled(true)
        try {
            const { data } = await authAxios.post(`v1/diagram/${diagram}/node/${node.id}/generate_attribute/?name=${attribute?.name}&type=${attribute?.type}&description=${attribute?.description}&model=${selectedLLMOption.value}`);
            update({ ...attribute, body: data })
            setOpenGenerateModal(false);
        } catch (error) {
            setGenerationError("Failed to generate method: API call failed.");
        } finally {
            setGenerateButtonDisabled(false)
        }
    }
    return (
        <div className="bg-stone-100">
            <div
                className={[
                    style.attribute,
                    create && style.new,
                    dirty && style.dirty,
                ]
                    .filter(Boolean)
                    .join(" ")}
            >
                <Tooltip
                    size="sm"
                    placement="left"
                    title={aiManaged
                        ? "Not available: an AI-managed attribute is stored as a database column, so it cannot also be a derived property."
                        : `Make attribute ${attribute?.derived ? "public" : "derived"}`
                    }
                >
                    <span>
                        <button
                            className="p-2"
                            disabled={aiManaged}
                            style={aiManaged ? { opacity: 0.4, cursor: "not-allowed" } : undefined}
                            onClick={() => {
                                if (aiManaged) return;
                                update({ ...attribute, derived: !attribute?.derived });
                            }}
                        >
                            {attribute?.derived ? "/" : "+"}
                        </button>
                    </span>
                </Tooltip>
                {attribute?.derived &&
                    <Tooltip
                        size="sm"
                        placement="left"
                        title={`${openEditMenu ? "Close" : "Edit derived attribute logic"}`}
                    >
                        <button type="button" onClick={() => { setOpenEditMenu((openEditMenu) => !openEditMenu) }}>
                            {openEditMenu ? <PanelTopClose size={16} /> : <Pencil size={16} />}
                        </button>
                    </Tooltip>
                }
                <input
                    type="text"
                    value={attribute?.name}
                    onChange={(e) => update({ ...attribute, name: e.target.value })}
                ></input>
                <span className="p-2">:</span>
                <Select
                    value={
                        selectOptions.find((option) =>
                            attribute?.type === "enum"
                                ? option.id === attribute?.enum
                                : option.value === attribute?.type
                        )
                    }
                    options={selectOptions}
                    getOptionValue={(option) => option.id}
                    getOptionLabel={(option) => option.label}
                    onChange={handleSelectChange}
                    className="w-80"
                />
                <button type="button" onClick={del} className={style.delete}>
                    <X size={12} />
                </button>
            </div>
            {attribute?.derived && openEditMenu &&
                <div className="">
                    <Editor
                        value={attribute?.body}
                        language="python"
                        options={{
                            lineNumbers: "off",
                            folding: false,
                        }}
                        height="12rem"
                        width="100%"
                        onChange={(e) => update({ ...attribute, body: e ?? "" })}
                    />
                </div>
            }
            {attribute?.derived && !openGenerateModal && openEditMenu &&
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
            {attribute?.derived && openGenerateModal && openEditMenu && (
                <div>
                    <form
                        id="generate-attribute"
                        className="flex min-w-96 flex-col gap-2"
                        onSubmit={generateAttribute}
                    >
                        <FormControl required>
                            <FormLabel>Description</FormLabel>
                            <Textarea
                                name="description"
                                placeholder="Describe how the attribute value should be derived, and how other attributes are used in this process"
                                minRows={4}
                                maxRows={4}
                                required
                                value={attribute?.description}
                                onChange={(e) =>
                                    update({ ...attribute, description: e.target.value })
                                }
                            />
                        </FormControl>
                    </form>
                    <div className="flex flex-row gap-4 pt-1">
                        <Button form="generate-attribute" type="submit" disabled={!attribute?.description || generateButtonDisabled}>
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
            <AiConfigSection
                attribute={attribute}
                className={node?.data?.name ?? ""}
                update={update}
            />
        </div>
    );
};

export default EditAttribute;
