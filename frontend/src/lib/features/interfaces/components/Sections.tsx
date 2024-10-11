import {
    Divider,
    FormControl,
    Input,
} from "@mui/joy";
import Chip from '@mui/joy/Chip';
import { Ban, Pencil, Plus, Save, Trash } from "lucide-react";
import Multiselect from 'multiselect-react-dropdown';
import React, { useState } from 'react';
import { useParams } from "react-router";
import { useClassAttributes, useClassCustomMethods, useSystemClasses } from "../queries";
import useLocalStorage from './useLocalStorage';

type Props = {
    projectId: string;
    systemId: string;
    app_comp: string;
    interfaceId: string;
    componentId: string;
};

export const Sections: React.FC<Props> = ({ app_comp }) => {
    const { systemId } = useParams();
    const [data, setData, isSuccess] = useLocalStorage('sections', []);
    const [editIndex, setEditIndex] = useState(-1);
    const [newName, setNewName] = useState('');
    const [selectedOperations, setSelectedOperations] = useLocalStorage('selectedOperations', []);
    const [pencelClick, setPencelClick] = useState(false);
    const [classes, isSuccessClasses] = useSystemClasses(systemId);
    const [selectedClass, setSelectedClass] = useLocalStorage('selectedClass', '');
    const [classAttributes] = useClassAttributes(systemId, selectedClass);
    const [classCustomMethods] = useClassCustomMethods(systemId, selectedClass)
    //const [attributes, setAttributes] = useState([]);
    const [selectedAttributes, setSelectedAttributes] = useLocalStorage('selectedAttributes', []);
    const [selectedCustomMethods, setSelectedCustomMethods] = useLocalStorage('selectedCustomMethods', [])


    const handleEdit = async (index: number) => {
        // Close name editor when switching section component
        if (pencelClick) {
            setPencelClick(false);
        }

        // Retrieve local storage vars from data
        if (data[index].class) {
            const classId = data[index].class;
            setSelectedClass(classId);
        }

        if (data[index].operations) {
            setSelectedOperations(data[index].operations);
        } else {
            setSelectedOperations([]);
        }

        if (data[index].attributes) {
            setSelectedAttributes(data[index].attributes);
        } else {
            setSelectedAttributes([]);
        }

        if (data[index].methods) {
            setSelectedCustomMethods(data[index].methods);
        } else {
            setSelectedCustomMethods([]);
        }

        setEditIndex(index);
    };

    const handleNameChange = (index: number) => {
        const newData = [...data];
        newData[index].name = newName;
        setData(newData);
        setPencelClick(false);
    };

    const handlePencilClick = () => {
        setPencelClick(true);
    }

    const handleNameCancel = () => {
        setPencelClick(false);
    };

    const handleMinus = () => {
        setEditIndex(-1);
    };

    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setNewName(event.target.value);
    };

    const handleDelete = (index: number) => {
        const newData = [...data];
        newData.splice(index, 1);
        setData(newData);
        setEditIndex(-1);
    };

    const toggleOperation = (sectionIndex: number, operation: 'create' | 'update' | 'delete') => {
        const sectionOperations = selectedOperations || {};
        const updatedOperations = {
            ...sectionOperations,
            [operation]: !sectionOperations[operation],
        };
        setSelectedOperations(updatedOperations);
        const newData = [...data];
        newData[sectionIndex].operations = updatedOperations;
        setData(newData);
    };

    const toggleClass = async (sectionIndex: number, cls) => {
        setSelectedClass(cls.id);
        const newData = [...data];
        newData[sectionIndex].class = cls.id;
        setSelectedAttributes([]);
        newData[sectionIndex].attributes = [];
        setData(newData);
    };

    const handleAttributeSelect = (selectedList, selectedItem, sectionIndex: number) => {
        const updatedAttributes = [...selectedAttributes, selectedItem];
        setSelectedAttributes(updatedAttributes);
        const newData = [...data];
        newData[sectionIndex].attributes = updatedAttributes;
        setData(newData);
    };

    const handleAttributeRemove = (selectedList, selectedItem, sectionIndex: number) => {
        const updatedAttributes = selectedAttributes.filter(attr => attr !== selectedItem);
        setSelectedAttributes(updatedAttributes);
        const newData = [...data];
        newData[sectionIndex].attributes = updatedAttributes;
        setData(newData);
    };

    const handleCustomMethodSelect = (selectedList, selectedItem, sectionIndex: number) => {
        const updatedCustomMethods = [...selectedCustomMethods, selectedItem];
        setSelectedCustomMethods(updatedCustomMethods);
        const newData = [...data];
        newData[sectionIndex].methods = updatedCustomMethods;
        setData(newData);
    };

    const handleCustomMethodRemove = (selectedList, selectedItem, sectionIndex: number) => {
        const updatedCustomMethods = selectedCustomMethods.filter(attr => attr !== selectedItem);
        setSelectedCustomMethods(updatedCustomMethods);
        const newData = [...data];
        newData[sectionIndex].methods = updatedCustomMethods;
        setData(newData);
    };

    return (
        <>
            {isSuccess && (
                <div className="flex flex-wrap gap-4">
                    {data.map((section, index) => (
                        <div key={index} className="flex flex-col gap-2">
                            {editIndex === index ? (
                                <div className="w-[240px] flex flex-col gap-2 space-y-2">
                                    <div>
                                        <h3 className="text-xl font-bold">Name</h3>
                                        {!pencelClick && (
                                            <div className="flex flex-wrap gap-2">
                                                <h2 className="text-l">{section.name}</h2>
                                                <Pencil
                                                    className="cursor-pointer ml-auto"
                                                    onClick={handlePencilClick}
                                                />
                                            </div>
                                        )}

                                        {pencelClick && (
                                            <FormControl required className="space-y-1">
                                                <Input
                                                    type="text"
                                                    value={newName}
                                                    onChange={handleInputChange}
                                                />
                                                <div className="flex flex-wrap gap-2 ml-auto">
                                                    <button
                                                        onClick={() => handleNameChange(index)}
                                                        className="w-[40px] h-[40px] bg-blue-500 text-white px-2 py-1 rounded-md hover:bg-blue-600"
                                                    >
                                                        <Save />
                                                    </button>
                                                    <button
                                                        onClick={handleNameCancel}
                                                        className="w-[40px] h-[40px] bg-gray-300 text-gray-700 px-2 py-1 rounded-md hover:bg-gray-400"
                                                    >
                                                        <Ban />
                                                    </button>
                                                </div>
                                            </FormControl>
                                        )}
                                    </div>
                                    <div className="space-y-1">
                                        <h3 className="text-xl font-bold">Primary Class</h3>
                                        <div className="flex gap-2">
                                            {isSuccessClasses && (
                                                classes.map((e) => (
                                                    <Chip
                                                        key={e.id}
                                                        onClick={() => toggleClass(index, e)}
                                                        color={selectedClass === e.id ? 'primary' : 'neutral'}
                                                    >
                                                        {e.data.name}
                                                    </Chip>
                                                )
                                                ))}
                                        </div>
                                    </div>
                                    <div className="space-y-1">
                                        <h3 className="text-xl font-bold">Operations</h3>
                                        <div className="flex gap-2">
                                            <Chip
                                                onClick={() => toggleOperation(index, 'create')}
                                                color={selectedOperations.create ? 'primary' : 'neutral'}
                                            >
                                                Create
                                            </Chip>
                                            <Chip
                                                onClick={() => toggleOperation(index, 'update')}
                                                color={selectedOperations.update ? 'primary' : 'neutral'}
                                            >
                                                Update
                                            </Chip>
                                            <Chip
                                                onClick={() => toggleOperation(index, 'delete')}
                                                color={selectedOperations.delete ? 'primary' : 'neutral'}
                                            >
                                                Delete
                                            </Chip>
                                        </div>
                                    </div>
                                    <div className='space-y-1'>
                                        <h3 className="text-xl font-bold">Attributes</h3>
                                        <Multiselect
                                            options={classAttributes}
                                            displayValue='name'
                                            placeholder="Select attributes..."
                                            showCheckbox={true}
                                            style={{ chips: { background: 'rgb(231 229 228)', color: 'rgb(61 56 70)' } }}
                                            selectedValues={selectedAttributes}
                                            onSelect={(selectedList, selectedItem) => handleAttributeSelect(selectedList, selectedItem, index)}
                                            onRemove={(selectedList, selectedItem) => handleAttributeRemove(selectedList, selectedItem, index)}
                                        />
                                    </div>
                                    <FormControl className="space-y-1">
                                        <h3 className="text-xl font-bold">Text</h3>
                                    </FormControl>
                                    <FormControl className="space-y-1">
                                        <h3 className="text-xl font-bold">Custom Operations</h3>
                                        <Multiselect
                                            options={classCustomMethods}
                                            displayValue='name'
                                            placeholder="Select methods..."
                                            showCheckbox={true}
                                            style={{ chips: { background: 'rgb(231 229 228)', color: 'rgb(61 56 70)' } }}
                                            selectedValues={selectedCustomMethods}
                                            onSelect={(selectedList, selectedItem) => handleCustomMethodSelect(selectedList, selectedItem, index)}
                                            onRemove={(selectedList, selectedItem) => handleCustomMethodRemove(selectedList, selectedItem, index)}
                                        />
                                    </FormControl>
                                    <Divider />
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => handleDelete(index)}
                                            className="w-[40px] h-[40px] bg-red-500 text-white px-2 py-1 rounded-md hover:bg-red-600"
                                        >
                                            <Trash />
                                        </button>
                                        <button
                                            onClick={handleMinus}
                                            className="w-[60px] h-[40px] bg-stone-200 text-stone-900 px-2 py-1 rounded-md hover:bg-blue-600"
                                        >
                                            Close
                                        </button>
                                    </div>
                                </div>
                            ) : (
                                <div className="flex justify-between items-center w-full">
                                    <h3
                                        onClick={() => handleEdit(index)}
                                        className="flex h-fit w-58 flex-col gap-2 overflow-hidden text-ellipsis rounded-md bg-stone-200 p-4 hover:bg-stone-300 cursor-pointer"
                                    >
                                        {section.name}
                                    </h3>
                                </div>
                            )}
                        </div>
                    ))}
                    <button
                        onClick={() => {
                            const newSection = { id: window.crypto.randomUUID(), name: `Section Component ${data.length + 1}`, class: "", operations: { "create": false, "update": false, "delete": false }, attributes: [] };

                            // Automatically use first class for new section component
                            if (isSuccessClasses && classes[0].id) {
                                newSection.class = classes[0].id;
                            }
                            setData([...data, newSection]);
                        }}
                        className="flex h-fit w-14 flex-col gap-2 overflow-hidden text-ellipsis rounded-md bg-stone-200 p-4 hover:bg-stone-300"
                    >
                        <Plus />
                    </button>
                </div>
            )}
        </>
    );
};

export default Sections;
