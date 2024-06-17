import React, { useState } from 'react'
import {
    Button,
    Divider,
    FormControl,
    Input,
    Select,
    Option,
} from "@mui/joy"
import { Plus } from "lucide-react";


type Props = {
    projectId: string
    systemId: string
    interfaceId: string
    componentId: string
}

export const Styling: React.FC<Props> = ({ app_comp }) => {

    const [radius, setRadius] = useState(0);
    const [backgroundColor, setBackgroundColor] = useState("#000000");
    const [textColor, setTextColor] = useState("#FFFFFF");
    const [accentColor, setAccentColor] = useState("#777777");
    const [selectedStyle, setSelectedStyle] = useState('');
    const [logoFile, setLogoFile] = useState(null);
    const [logoDimensions, setLogoDimensions] = useState({ width: 0, height: 0 });

    const handleRadiusChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const value = parseInt(event.target.value, 10);
        if (value >= 0 && value <= 10) {
            setRadius(value);
        }
    }
    const handleBackgroundColorChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setBackgroundColor(event.target.value);
    }

    const handleTextColorChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setTextColor(event.target.value);
    }

    const handleAccentColorChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setAccentColor(event.target.value);
    }
    const handleStyleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        setSelectedStyle(event.target.value);
    }

    const handleLogoChange = (event) => {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const img = new Image();
                img.onload = function() {
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
    };


    return (
        <>
            <div className="max-w-[300px] mx-auto mt-4 ml-2 space-y-4">
                <FormControl>
                    <h3 className="text-xl font-bold">Logo</h3>
                    <input
                        type="file"
                        accept="image/*"
                        onChange={handleLogoChange}
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
                            value={backgroundColor}
                            onChange={handleBackgroundColorChange}
                            pattern="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"
                            placeholder="#777777"
                        />
                        <input
                            type="color" 
                            value={backgroundColor}
                            onChange={handleBackgroundColorChange}
                            className="w-[50px] h-[50px] border border-gray-500 p-0"
                            style={{ backgroundColor: backgroundColor }}
                        />
                    </div>
                </FormControl>

                <FormControl>
                    <h3 className="text-xl font-bold">Text color</h3>
                    <div className="flex w-full flex-row justify-between pb-1">
                        <Input 
                            type="text" 
                            value={textColor}
                            onChange={handleTextColorChange}
                            pattern="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"
                            placeholder="#777777"
                        />
                        <input
                            type="color" 
                            value={textColor}
                            onChange={handleTextColorChange}
                            className="w-[50px] h-[50px] border border-gray-500 p-0"
                            style={{ backgroundColor: textColor }}
                        />
                    </div>
                </FormControl>

                <FormControl>
                    <h3 className="text-xl font-bold">Accent color</h3>
                    <div className="flex w-full flex-row justify-between pb-1">
                        <Input 
                            type="text" 
                            value={accentColor}
                            onChange={handleAccentColorChange}
                            pattern="^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"
                            placeholder="#777777"
                        />
                        <input
                            type="color" 
                            value={accentColor}
                            onChange={handleAccentColorChange}
                            className="w-[50px] h-[50px] border border-gray-500 p-0"
                            style={{ backgroundColor: accentColor }}
                        />
                    </div>
                </FormControl>

                <FormControl required>
                    <h3 className="text-xl font-bold">Radius</h3>
                    <Input 
                        type="number"
                        value={radius} 
                        onChange={handleRadiusChange}
                        min={0}
                        max={10}
                        required 
                    />
                </FormControl>
                <Divider />
                <div className="flex flex-row pt-1">
                    <Button form="update-syling" type="submit">
                        Submit
                    </Button>
                </div>
            </div>
        </>
    )
}

export default Styling