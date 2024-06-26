import React, { useState, useEffect } from 'react';
import { Plus, Trash, Save, Ban, Pencil } from "lucide-react";
import useLocalStorage from './useLocalStorage';
import {
    FormControl,
    Input,
    Select,
    Option,
    Divider,
} from "@mui/joy"
import Multiselect from 'multiselect-react-dropdown';

type Props = {
    projectId: string;
    systemId: string;
    interfaceId: string;
    componentId: string;
};

export const Pages: React.FC<Props> = ({ app_comp }) => {
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

    const handleEdit = (index: number) => {
        setEditIndex(index);
        setNewName(data[index].name);
    };

    const handleSave = (index: number) => {
        const newData = [...data];
        newData[index].name = newName;
        newData[index].category = selectedCategory;
        newData[index].sections = selectedSections;
        setData(newData);
    };

    const handleMinus = () => {
        setEditIndex(-1);
    };

    const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setNewName(event.target.value);
    };

    const handleCategoryChange = (event, newValue, pageIndex: number) => {
        setSelectedCategory(newValue as string);
        const newData = [...data];
        newData[pageIndex].category = newValue;
        setData(newData);
    };

    const handleDelete = (index: number) => {
        const newData = [...data];
        newData.splice(index, 1);
        setData(newData);
        setEditIndex(-1);
    };

    
    const handleSectionSelect = (selectedList, selectedItem, pageIndex: sint) => {
        if (!selectedSections) {
            setSelectedSections([]);
        }
        selectedSections.push(selectedItem);
        setSelectedSections(selectedSections);
        handleSave(pageIndex);
    };

    const handleSectionRemove = (selectedList, selectedItem, pageIndex: int) => {
        if (!selectedSections) {
            setSelectedSections([]);
        }
        selectedSections.pop(selectedItem);
        setSelectedSections(selectedSections);
        handleSave(pageIndex);
    };

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
                                                    placeholder="Choose one…"
                                                    value={selectedCategory}
                                                    onChange={(event, newValue) => handleCategoryChange(event, newValue, index)}
                                                >
                                                    {categories.map((e) => (
                                                        <Option key={e.name} value={e.name}>{e.name}</Option>
                                                    ))}
                                                </Select>
                                            ) : (
                                                <p>Create a new category!</p>
                                            )}
                                        </FormControl>
                                    )}
                                    {isSuccessSections && (
                                        <div className='space-y-1'>
                                            <h3 className="text-xl font-bold">Section Components</h3>
                                            <Multiselect
                                                options={sections}
                                                displayValue='name'
                                                placeholder="Select sections..."
                                                showCheckbox={true}
                                                style={{chips:{background:'rgb(231 229 228)',color:'rgb(61 56 70)'}}}
                                                selectedValues={selectedSections}
                                                onSelect={(selectedList, selectedItem) => handleSectionSelect(selectedList, selectedItem, index)}
                                                onRemove={(selectedList, selectedItem) => handleSectionRemove(selectedList, selectedItem, index)}
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
                        const newPage = { name: `Page ${data.length + 1}` };
                        setData([...data, newPage]);
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