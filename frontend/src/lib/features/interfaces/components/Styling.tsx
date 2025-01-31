import {
    FormControl,
    Input,
    Option,
    Select,
} from "@mui/joy";
import { Plus } from "lucide-react";
import React, { useEffect } from 'react';
import useLocalStorage from './useLocalStorage';


type Props = {
}

export const Styling: React.FC<Props> = () => {

    const [data, setData, isSuccess] = useLocalStorage('styling', '');
    const [logoFile, setLogoFile] = useLocalStorage('logoFile', null);
    const [logoDimensions, setLogoDimensions] = useLocalStorage('logoDimensions', { width: 0, height: 0 });

    useEffect(() => {
        if (!data || Object.keys(data).length === 0) {
            const defaultStyling = {
                radius: 0,
                backgroundColor: '#FFFFFF',
                textColor: '#000000',
                accentColor: '#F5F5F4',
                selectedStyle: 'modern'
            };
            setData(defaultStyling);
        }
    }, [data, setData]);

    const handleRadiusChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const value = parseInt(event.target.value, 10);
        if (value >= 0 && value <= 10) {
            const newData = { ...data, radius: value };
            setData(newData);
        }
    }

    const handleBackgroundColorChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const newData = { ...data, backgroundColor: event.target.value };
        setData(newData);
    }

    const handleTextColorChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const newData = { ...data, textColor: event.target.value };
        setData(newData);
    }

    const handleAccentColorChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const newData = { ...data, accentColor: event.target.value };
        setData(newData);
    }

    const handleStyleChange = (event, newValue) => {
        const newData = { ...data, selectedStyle: newValue };
        setData(newData);
    };

    /*const handleLogoChange = (event) => {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function (e) {
                const img = new Image();
                img.onload = function () {
                    const maxWidth = 512;
                    const maxHeight = 512;
                    const width = img.width;
                    const height = img.height;
                    if (width <= maxWidth && height <= maxHeight) {
                        setLogoFile(file);
                        setLogoDimensions({ width, height });
                    } else {
                        alert(`Maximum allowed dimensions: ${maxWidth} x ${maxHeight} px.`);
                    }
                };
                img.src = e.target.result;
            };
            reader.readAsDataURL(file);
        }
    };*/

    return (
        <>
            {isSuccess && (
                <div className="max-w-[300px] mx-auto mt-4 ml-2 space-y-4">
                    <FormControl>
                        <h3 className="text-xl font-bold">Logo</h3>
                        <input
                            type="file"
                            accept="image/*"
                            //onChange={handleLogoChange}
                            className="hidden"
                            id="logoInput"
                        />
                        <label htmlFor="logoInput" className="cursor-pointer">
                            <Plus />
                            {logoFile ? `${logoFile.name} (${logoDimensions.width}x${logoDimensions.height}px)` : ''}
                        </label>
                    </FormControl>

                    <FormControl required>
                        <h3 className="text-xl font-bold">Style</h3>
                        <Select
                            placeholder="Choose one…"
                            value={data.selectedStyle}
                            onChange={handleStyleChange}
                        >
                            <Option value="basic">Basic</Option>
                            <Option value="modern">Modern</Option>
                            <Option value="abstract">Abstract</Option>
                        </Select>
                    </FormControl>

                    <FormControl>
                        <h3 className="text-xl font-bold">Background color</h3>
                        <div className="flex w-full flex-row justify-between pb-1">
                            <Input
                                type="text"
                                value={data.backgroundColor}
                                onChange={handleBackgroundColorChange}
                                //pattern="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"
                                placeholder="#FFFFFF"
                            />
                            <input
                                type="color"
                                value={data.backgroundColor}
                                onChange={handleBackgroundColorChange}
                                className="w-[50px] h-[50px] border border-gray-500 p-0 cursor-pointer"
                                style={{ backgroundColor: data.backgroundColor }}
                            />
                        </div>
                    </FormControl>

                    <FormControl>
                        <h3 className="text-xl font-bold">Text color</h3>
                        <div className="flex w-full flex-row justify-between pb-1">
                            <Input
                                type="text"
                                value={data.textColor}
                                onChange={handleTextColorChange}
                                //pattern="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"
                                placeholder="#000000"
                            />
                            <input
                                type="color"
                                value={data.textColor}
                                onChange={handleTextColorChange}
                                className="w-[50px] h-[50px] border border-gray-500 p-0 cursor-pointer"
                                style={{ backgroundColor: data.textColor }}
                            />
                        </div>
                    </FormControl>

                    <FormControl>
                        <h3 className="text-xl font-bold">Accent color</h3>
                        <div className="flex w-full flex-row justify-between pb-1">
                            <Input
                                type="text"
                                value={data.accentColor}
                                onChange={handleAccentColorChange}
                                placeholder="#777777"
                            />
                            <input
                                type="color"
                                value={data.accentColor}
                                onChange={handleAccentColorChange}
                                className="w-[50px] h-[50px] border border-gray-500 p-0 cursor-pointer"
                                style={{ backgroundColor: data.accentColor }}
                            />
                        </div>
                    </FormControl>

                    <FormControl required>
                        <h3 className="text-xl font-bold">Radius</h3>
                        <Input
                            type="number"
                            value={data.radius}
                            onChange={handleRadiusChange}
                            required
                        />
                    </FormControl>
                </div>
            )}
        </>
    )
}

export default Styling
