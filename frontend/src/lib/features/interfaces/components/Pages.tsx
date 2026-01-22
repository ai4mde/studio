import {
    Divider,
    FormControl,
    Input,
} from "@mui/joy";
import { Ban, Pencil, Plus, Save, Trash } from "lucide-react";
import React, { useEffect, useState } from 'react';
import Select from "react-select";
import useLocalStorage from './useLocalStorage';

type Props = {
};

export const Pages: React.FC<Props> = () => {
    const [data, setData, isSuccess] = useLocalStorage('pages', []);
    const [editIndex, setEditIndex] = useState(-1);
    const [newName, setNewName] = useState('');
    const [categories, , isSuccessCategories] = useLocalStorage('categories', []);
    const [selectedCategory, setSelectedCategory] = useLocalStorage('selectedCategory', '');
    const [sections, isSuccessSections] = useLocalStorage('sections', []);
    const [selectedSections, setSelectedSections] = useLocalStorage('selectedSections', []);
    const [pencelClick, setPencelClick] = useState(false);

    useEffect(() => {
        if (editIndex !== -1 && data[editIndex].sections) {
            setSelectedSections(data[editIndex].sections);
        } else {
            setSelectedSections([]);
        }
    }, [editIndex, data]);

    useEffect(() => {
        if (editIndex !== -1 && data[editIndex].category) {
            setSelectedCategory(data[editIndex].category);
        } else {
            setSelectedCategory(null);
        }
    }, [editIndex, data]);

    const handleEdit = (index: number) => {
        setEditIndex(index);
        if (data[index]?.type) {
            setSelectedPageType(data[index].type);
        } else {
            setSelectedPageType({ label: 'Normal', value: 'normal' });
        }
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

    useEffect(() => {
        if (editIndex !== -1) {
            const newData = [...data];
            newData[editIndex].sections = selectedSections;
            setData(newData);
        }
    }, [selectedSections]);

    useEffect(() => {
        if (editIndex !== -1) {
            const newData = [...data];
            newData[editIndex].category = selectedCategory;
            setData(newData);
        }
    }, [selectedCategory]);


    const handlePencilClick = () => {
        setPencelClick(true);
    }

    const handleNameChange = (index: number) => {
        const newData = [...data];
        newData[index].name = newName;
        setData(newData);
        setPencelClick(false);
    };

    const handleNameCancel = () => {
        setPencelClick(false);
    };

    return (
        <>
            <div className="flex flex-wrap gap-4">
                {isSuccess && (
                    data.map((page, index) => (
                        <div key={index} className="flex flex-col gap-2">
                            {editIndex === index ? (
                                <div className="w-[240px] flex flex-col gap-2 space-y-2">
                                    <div>
                                        <h3 className="text-xl font-bold">Name</h3>
                                        {!pencelClick && (
                                            <div className="flex flex-wrap gap-2">
                                                <h2 className="text-l">{page.name}</h2>
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
                                    {isSuccessCategories && (
                                        <FormControl className="space-y-1">
                                            <h3 className="text-xl font-bold">Category</h3>
                                            {categories.length > 0 ? (
                                                <Select
                                                    name="category"
                                                    options={categories.map((e) => ({ label: e.name, value: e }))}
                                                    value={selectedCategory}
                                                    onChange={setSelectedCategory}
                                                    isClearable={true}
                                                />
                                            ) : (
                                                <p>Create a new category!</p>
                                            )}
                                        </FormControl>
                                    )}
                                    {isSuccessSections && (
                                        <div className='space-y-1'>
                                            <h3 className="text-xl font-bold">Section Components</h3>
                                            <Select
                                                isMulti
                                                name="sections"
                                                options={sections.map((e) => ({ label: e.name, value: e.id }))}
                                                value={selectedSections}
                                                onChange={setSelectedSections}
                                            />
                                        </div>

                                    )}
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
                                        className="flex h-fit w-48 flex-col gap-2 overflow-hidden text-ellipsis rounded-md bg-stone-200 p-4 hover:bg-stone-300 cursor-pointer"
                                    >
                                        {page.name}
                                    </h3>
                                </div>
                            )}
                        </div>
                    ))
                )}
                <button
                    onClick={() => {
                        const newPage = { id: window.crypto.randomUUID(), name: `Page ${data.length + 1}`, category: null, type: { label: 'Normal', value: 'normal' } };
                        setData([...data, newPage]);
                        setEditIndex(data.length);
                    }}
                    className="flex h-fit w-14 flex-col gap-2 overflow-hidden text-ellipsis rounded-md bg-stone-200 p-4 hover:bg-stone-300"
                >
                    <Plus />
                </button>
            </div>
        </>
    );
};

export default Pages;