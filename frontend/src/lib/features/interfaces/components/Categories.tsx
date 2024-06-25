import React, { useState } from 'react';
import { Plus, Trash, Save, Ban } from "lucide-react";
import useLocalStorage from './useLocalStorage';
import {
    FormControl,
    Input,
    Divider,
} from "@mui/joy"

type Props = {
    projectId: string;
    systemId: string;
    interfaceId: string;
    componentId: string;
};

export const Categories: React.FC<Props> = ({ app_comp }) => {
    const [data, setData, isSuccess] = useLocalStorage('categories', []);
    const [editIndex, setEditIndex] = useState(-1);
    const [newName, setNewName] = useState('');

    const handleEdit = (index: number) => {
        setEditIndex(index);
        setNewName(data[index].name);
    };

    const handleSave = (index: number) => {
        const newData = [...data];
        newData[index].name = newName;
        setData(newData);
        setEditIndex(-1);
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

    return (
        <>
            <div className="flex flex-wrap gap-4">
                {isSuccess && (
                    data.map((category, index) => (
                        <div key={index} className="flex flex-col gap-2">
                            {editIndex === index ? (
                                <div className="flex flex-col gap-2 space-y-3">
                                    <FormControl required className="space-y-1">
                                        <h3 className="text-xl font-bold">Name</h3>
                                            <Input 
                                                type="text" 
                                                value={newName}
                                                onChange={handleInputChange}
                                            />
                                    </FormControl>
                                    <Divider />
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => handleSave(index)}
                                            className="w-[40px] h-[40px] bg-blue-500 text-white px-2 py-1 rounded-md hover:bg-blue-600"
                                        >
                                            <Save />
                                        </button>
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
                                        className="flex h-fit w-48 flex-col gap-2 overflow-hidden text-ellipsis rounded-md bg-stone-200 p-4 hover:bg-stone-300 cursor-pointer"
                                    >
                                        {category.name}
                                    </h3>
                                </div>
                            )}
                        </div>
                    ))
                )}
                <button
                    onClick={() => {
                        const newCategory = { name: `Category ${data.length + 1}` };
                        setData([...data, newCategory]);
                        setEditIndex(-1);
                    }}
                    className="flex h-fit w-14 flex-col gap-2 overflow-hidden text-ellipsis rounded-md bg-stone-200 p-4 hover:bg-stone-300"
                >
                    <Plus />
                </button>
            </div>
        </>
    );
};

export default Categories;
