import React, { useState } from 'react';
import { Plus, Trash, Save, Ban, Pencil } from "lucide-react";
import useLocalStorage from './useLocalStorage';
import {
    FormControl,
    Input,
    Divider,
} from "@mui/joy";
import Chip from '@mui/joy/Chip';
import { useSystemClasses } from "../queries";
import { useParams } from "react-router";

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

    const handleEdit = (index: number) => {
        // Close name editor when switching section component
        if (pencelClick){
            setPencelClick(false);
        }

        // Automatically use first class for new section component
        if (!data[index].class && isSuccessClasses){
            toggleClass(index, classes[0].data.name);
        }

        // Retrieve local storage vars from data
        if (data[index].class) {
            setSelectedClass(data[index].class);
        }
        if (data[index].operations) {
            setSelectedOperations(data[index].operations);
        } else {
            setSelectedOperations([]);
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

    const toggleClass = (sectionIndex: number, cls: string) => {
        setSelectedClass(cls as string);
        const newData = [...data];
        newData[sectionIndex].class = cls;
        setData(newData);
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
                                                        onClick={() => toggleClass(index, e.data.name)}
                                                        color={selectedClass === e.data.name ? 'primary' : 'neutral'}
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
