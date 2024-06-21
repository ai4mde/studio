import React, { useState, useEffect } from 'react';
import { Plus, Trash, Save, Ban, Pencil } from "lucide-react";
import useLocalStorage from './useLocalStorage';
import {
    FormControl,
    Input,
    Divider,
} from "@mui/joy";
import Chip from '@mui/joy/Chip';

type Props = {
    projectId: string;
    systemId: string;
    interfaceId: string;
    componentId: string;
};

export const Sections: React.FC<Props> = ({ app_comp }) => {
    const [data, setData, isSuccess] = useLocalStorage('sections', []);
    const [editIndex, setEditIndex] = useState(-1);
    const [newName, setNewName] = useState('');
    const [selectedOperations, setSelectedOperations] = useLocalStorage('selectedOperations', {});
    const [pencelClick, setPencelClick] = useState(false);

    useEffect(() => {
        const storedOperations = JSON.parse(localStorage.getItem('selectedOperations') || '{}');
        setSelectedOperations(storedOperations);
    }, [setSelectedOperations]);

    const handleEdit = (index: number) => {
        setEditIndex(index);
        setNewName(data[index].name);
    };

    const handlePencilClick = () => {
        setPencelClick(true);
    }

    const handleSave = (index: number) => {
        const newData = [...data];
        newData[index].name = newName;
        setData(newData);
        setPencelClick(false);
    };

    const handleNameCancel = () => {
        setPencelClick(false);
    };

    const handleCancel = () => {
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
        const sectionOperations = selectedOperations[sectionIndex] || {};
        const updatedSectionOperations = {
            ...sectionOperations,
            [operation]: !sectionOperations[operation],
        };
        const updatedOperations = {
            ...selectedOperations,
            [sectionIndex]: updatedSectionOperations,
        };
        setSelectedOperations(updatedOperations);
        localStorage.setItem('selectedOperations', JSON.stringify(updatedOperations));
    };

    return (
        <>
            {isSuccess && (
                <div className="flex flex-wrap gap-4">
                    {data.map((section, index) => (
                        <div key={index} className="flex flex-col gap-2">
                            {editIndex === index ? (
                                <div className="flex flex-col gap-2 space-y-2">
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
                                                        onClick={() => handleSave(index)}
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
                                    <FormControl className="space-y-1">
                                        <h3 className="text-xl font-bold">Primary Class</h3>
                                    </FormControl>
                                    <FormControl className="space-y-1">
                                        <h3 className="text-xl font-bold">Operations</h3>
                                        <div className="flex gap-2">
                                            <Chip
                                                onClick={() => toggleOperation(index, 'create')}
                                                color={selectedOperations[index]?.create ? 'primary' : 'neutral'}
                                            >
                                                Create
                                            </Chip>
                                            <Chip
                                                onClick={() => toggleOperation(index, 'update')}
                                                color={selectedOperations[index]?.update ? 'primary' : 'neutral'}
                                            >
                                                Update
                                            </Chip>
                                            <Chip
                                                onClick={() => toggleOperation(index, 'delete')}
                                                color={selectedOperations[index]?.delete ? 'primary' : 'neutral'}
                                            >
                                                Delete
                                            </Chip>
                                        </div>
                                    </FormControl>
                                    <FormControl className="space-y-1">
                                        <h3 className="text-xl font-bold">Links</h3>
                                    </FormControl>
                                    <FormControl className="space-y-1">
                                        <h3 className="text-xl font-bold">Text</h3>
                                    </FormControl>
                                    <FormControl className="space-y-1">
                                        <h3 className="text-xl font-bold">Custom Operations</h3>
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
                                            onClick={handleCancel}
                                            className="w-[40px] h-[40px] bg-gray-300 text-gray-700 px-2 py-1 rounded-md hover:bg-gray-400"
                                        >
                                            <Ban />
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
                            const newSection = { name: `Section Component ${data.length + 1}` };
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
