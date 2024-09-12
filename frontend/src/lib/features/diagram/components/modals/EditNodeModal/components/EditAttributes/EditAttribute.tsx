import { X } from "lucide-react";
import React, { useState, useEffect } from "react";
import style from "./editattributes.module.css";
import Select from "react-select";
import { Tooltip } from "@mui/joy";
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
            console.log(updatedAttribute);
        }
        else {
            let updatedAttribute = {
                ...attribute,
                type: selectedOption.value,
                enum: null
            };
            update(updatedAttribute);
            console.log(updatedAttribute);
        }
    }

    return (
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
    );
};

export default EditAttribute;
