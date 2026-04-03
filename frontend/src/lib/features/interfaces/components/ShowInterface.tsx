import { authAxios } from '$auth/state/auth';
import { deleteInterface } from '$browser/mutations';
import { useInterface } from "$browser/queries";
import {
    CircularProgress,
    Tab,
    TabList,
    TabPanel,
    Tabs,
} from '@mui/joy';
import CryptoJS from 'crypto-js';
import { CircleUserRound, Layers, Save, Trash } from "lucide-react";
import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Categories } from './Categories';
import { Pages } from './Pages';
import { Sections } from './Sections';
import { Styling } from './Styling';
import { Settings } from './Settings';
import AIGeneration from './AIGeneration';


type Props = {
    systemId: string;
    app_comp: string;
};

const ShowInterface: React.FC<Props> = ({ app_comp }) => {
    const { data, isSuccess, refetch } = useInterface(app_comp);
    const navigate = useNavigate();
    const { systemId } = useParams();
    const [isSaving, setIsSaving] = useState(false);
    const [isGenerating, setIsGenerating] = useState(false);
    const [generateError, setGenerateError] = useState<string | null>(null);
    //const actorId = data?.actor || '';
    //const [actor, isSuccessActor] = useActor(systemId, actorId);

    // Refresh data and update localStorage
    const handleAIUpdate = async () => {
        const result = await refetch();
        if (result.data?.data) {
            // data might be string or object
            const newData = typeof result.data.data === 'string' 
                ? JSON.parse(result.data.data) 
                : result.data.data;
            localStorage.setItem('styling', JSON.stringify(newData.styling || {}));
            localStorage.setItem('categories', JSON.stringify(newData.categories || []));
            localStorage.setItem('pages', JSON.stringify(newData.pages || []));
            localStorage.setItem('sections', JSON.stringify(newData.sections || []));
            localStorage.setItem('settings', JSON.stringify(newData.settings || {}));
        }
    };

    const handleDelete = async () => {
        try {
            await deleteInterface(app_comp);
        } catch (error) {
            console.error('Error deleting interface:', error);
        }
        navigate(`/systems/${systemId}/interfaces`);
    };

    const handleGeneratePrototype = async () => {
        if (!systemId || !data) return;
        setIsGenerating(true);
        setGenerateError(null);
        try {
            const [classifiers, relations, interfacesRes, diagramsRes] = await Promise.all([
                authAxios.get(`v1/metadata/systems/${systemId}/classes/`),
                authAxios.get(`v1/metadata/systems/${systemId}/classifier-relations/`),
                authAxios.get(`v1/metadata/interfaces/`, { params: { system: systemId } }),
                authAxios.get(`v1/diagram/system/${systemId}/`),
            ]);

            const allInterfaces: any[] = interfacesRes.data || [];
            const interfaceNames = allInterfaces.map((e: any) => ({ name: e.name }));
            const inputString = `${systemId}${JSON.stringify(classifiers.data)}${JSON.stringify(relations.data)}${JSON.stringify(interfaceNames)}`;
            const databaseHash = CryptoJS.SHA256(inputString).toString(CryptoJS.enc.Hex);

            const prototypeName = data.name.replace(/[^a-zA-Z0-9]/g, '');
            const metadata = {
                diagrams: diagramsRes.data || [],
                interfaces: allInterfaces.map((e: any) => ({ label: e.name, value: e })),
                useAuthentication: true,
            };

            await authAxios.post(`v1/generator/prototypes/?database_prototype_name=`, {
                name: prototypeName,
                description: `Prototype generated from interface ${data.name}`,
                system_id: systemId,
                metadata,
                database_hash: databaseHash,
            });

            navigate(`/systems/${systemId}/prototypes`);
        } catch (error) {
            console.error('Error generating prototype:', error);
            setGenerateError('Failed to generate prototype. Please try again.');
        } finally {
            setIsGenerating(false);
        }
    };

    const handleSave = async () => {
        const styling = JSON.parse(localStorage.getItem('styling')) || {};
        const categories = JSON.parse(localStorage.getItem('categories')) || [];
        const pages = JSON.parse(localStorage.getItem('pages')) || [];
        const sections = JSON.parse(localStorage.getItem('sections')) || [];
        const settings = JSON.parse(localStorage.getItem('settings')) || {};

        setIsSaving(true);
        try {
            await authAxios.put(`/v1/metadata/interfaces/${app_comp}/`, {
                id: app_comp,
                name: data?.name,
                description: data?.description,
                system_id: systemId,
                data: {
                    "styling": styling,
                    "categories": categories,
                    "pages": pages,
                    "sections": sections,
                    "settings": settings,
                },
            });
        } catch (error) {
            console.error('Error saving interface:', error);
        } finally {
            setTimeout(function () {
                setIsSaving(false);
            }, 200);
        }
    };

    return (
        <>
            {isSuccess && (
                <>
                    <div className="flex items-center justify-between w-full gap-4">
                        <span>
                            <h3 className="text-xl font-bold">{data.name}</h3>
                            <span className='flex items-center gap-1'>
                                <h4 className="text-l">{data.actor || 'Unknown'}</h4>
                                <CircleUserRound size={20} />
                            </span>
                        </span>
                        <div className="flex gap-4 ml-auto">
                            <AIGeneration interfaceId={app_comp} onUpdate={handleAIUpdate} />
                            <button
                                onClick={handleGeneratePrototype}
                                disabled={isGenerating}
                                title={generateError || undefined}
                                className="h-[40px] bg-green-500 text-white px-3 py-1 rounded-md hover:bg-green-600 flex items-center justify-center gap-2 disabled:opacity-60"
                            >
                                {isGenerating ? <CircularProgress className="animate-spin" /> : <Layers size={18} />}
                                Generate Prototype
                            </button>
                            <button
                                onClick={handleSave}
                                className="w-[40px] h-[40px] bg-blue-500 text-white px-2 py-1 rounded-md hover:bg-blue-600 flex items-center justify-center"
                                disabled={isSaving}
                            >
                                {isSaving ? <CircularProgress /> : <Save />}
                            </button>
                            <button
                                onClick={handleDelete}
                                className="w-[172px] h-[40px] bg-red-500 text-white px-2 py-1 rounded-md hover:bg-red-600 flex items-center justify-center gap-2"
                            >
                                <Trash />
                                Delete Interface
                            </button>
                        </div>
                    </div>
                    <Tabs>
                        <TabList>
                            <Tab>Fragment</Tab>
                            <Tab>Categories</Tab>
                            <Tab>Pages</Tab>
                            <Tab>Section Components</Tab>
                            <Tab>Styling</Tab>
                            <Tab>Settings</Tab>
                        </TabList>
                        <TabPanel value={0}>
                            <p>Fragment</p>
                        </TabPanel>
                        <TabPanel value={1}>
                            <Categories />
                        </TabPanel>
                        <TabPanel value={2}>
                            <Pages actorName = {data?.name}/>
                        </TabPanel>
                        <TabPanel value={3}>
                            <Sections />
                        </TabPanel>
                        <TabPanel value={4}>
                            <Styling interfaceId={app_comp} />
                        </TabPanel>
                        <TabPanel value={5}>
                            <Settings />
                        </TabPanel>
                    </Tabs>
                </>
            )}
        </>
    );
};

export default ShowInterface;
