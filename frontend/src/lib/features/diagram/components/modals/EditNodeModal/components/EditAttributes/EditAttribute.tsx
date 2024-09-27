import Editor from "@monaco-editor/react";
import { X, Pencil, PanelTopClose } from "lucide-react";
import React, { useState, useEffect } from "react";
import style from "./editattributes.module.css";
import Select from "react-select";
import { Tooltip, Button, FormControl, FormLabel, Textarea } from "@mui/joy";
import { Node } from "reactflow";
import { authAxios } from "$lib/features/auth/state/auth";
import { useDiagramStore } from "$diagram/stores";

const EditAttribute: React.FC<{
    attribute: any;
    update: (v: any) => void;
    del: () => void;
    dirty?: boolean;
    create?: boolean;
    node: Node;
}> = ({ attribute, del, update, dirty, create, node }) => {
    const [ enumClassifiers, setEnumClassifiers ] = useState([]);
    const { diagram } = useDiagramStore();
    const [openEditMenu, setOpenEditMenu] = useState(false);
    const [openGenerateModal, setOpenGenerateModal] = useState(false);
    const [generationError, setGenerationError] = useState<string | null>(null);
    const LLMOptions = [
        { value: 'GPT-4o', label: 'GPT-4o' },
    ]
    const [generateButtonDisabled, setGenerateButtonDisabled] = useState(false);


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
    const handleSelectChange = (selectedOption) =>{
        console.log('Selected value:', selectedOption.value); // Access the value
        setSelectedOption(selectedOption);
        if (selectedOption.value === "enum"){
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
            const { data } = await authAxios.post(`v1/diagram/${diagram}/node/${node.id}/generate_method/?name=${attribute?.name}&type=${attribute?.type}&description=${attribute?.description}`);
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
                    title={`Make attribute ${
                        attribute?.derived ? "public" : "derived"
                    }`}
                >
                    <button
                        className="p-2"
                        onClick={() => {
                            update({ ...attribute, derived: !attribute?.derived });
                        }}
                    >
                        {attribute?.derived ? "/" : "+"}
                    </button>
                </Tooltip>
                { attribute?.derived &&
                    <Tooltip
                        size="sm"
                        placement="left"
                        title={`${openEditMenu ? "Close" : "Edit derived attribute logic"}`}
                    >
                        <button type="button" onClick={() => {setOpenEditMenu((openEditMenu) => !openEditMenu)}}>
                            { openEditMenu ? <PanelTopClose size={16} /> : <Pencil size={16} /> }
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
            { attribute?.derived && openEditMenu && 
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
            { attribute?.derived && !openGenerateModal && openEditMenu &&
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
                            value={LLMOptions[0]}
                        />
                        <button type="button" onClick={() => {setOpenGenerateModal(false);setGenerationError(null);}}>
                            <X size={20}/>
                        </button>
                    </div>
                    {generationError && <p style={{ color: 'red' }}>{generationError}</p>}
                </div>
            )}
        </div>
    );
};

export default EditAttribute;
