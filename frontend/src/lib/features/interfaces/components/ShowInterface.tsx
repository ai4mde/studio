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
import { CircleUserRound, LayoutGrid, Save, Trash, Wand2 } from "lucide-react";
import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { Categories } from './Categories';
import { Pages } from './Pages';
import { Sections } from './Sections';
import { Styling } from './Styling';
import { Settings } from './Settings';
import InterfaceGenerate from './InterfaceGenerate';
import Fragment from './Fragment';


type Props = {
    systemId: string;
    app_comp: string;
};

const ShowInterface: React.FC<Props> = ({ app_comp }) => {
    const { data, isSuccess } = useInterface(app_comp);
    const navigate = useNavigate();
    const { systemId } = useParams();
    const [searchParams] = useSearchParams();
    const defaultTab = searchParams.get("tab") === "ai-generate" ? 6 : 0;
    const [isSaving, setIsSaving] = useState(false);
    const [liveTheme, setLiveTheme] = useState(null);
    const [layoutKey, setLayoutKey] = useState(0);
    const [autoLayoutDone, setAutoLayoutDone] = useState(false);

    // Seed liveTheme from server data once loaded
    useEffect(() => {
        if (isSuccess && data?.data?.theme && !liveTheme) {
            setLiveTheme(data.data.theme);
        }
    }, [isSuccess]);

    const handleAutoLayout = () => {
        if (!data?.data) return;
        const { pages, sections, categories, styling, settings } = data.data;
        if (pages?.length)      localStorage.setItem('pages',      JSON.stringify(pages));
        if (sections?.length)   localStorage.setItem('sections',   JSON.stringify(sections));
        if (categories?.length) localStorage.setItem('categories', JSON.stringify(categories));
        if (styling)            localStorage.setItem('styling',    JSON.stringify(styling));
        if (settings)           localStorage.setItem('settings',   JSON.stringify(settings));
        setAutoLayoutDone(true);
        setLayoutKey(k => k + 1);
    };

    const handleDelete = async () => {
        try {
            await deleteInterface(app_comp);
        } catch (error) {
            console.error('Error deleting interface:', error);
        }
        navigate(`/systems/${systemId}/interfaces`);
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
                    ...(liveTheme && { "theme": liveTheme }),
                    ...(data?.data?.designerSession && { "designerSession": data.data.designerSession }),
                    ...(data?.data?.designerMeta && { "designerMeta": data.data.designerMeta }),
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
                            <button
                                onClick={handleAutoLayout}
                                title="Load pipeline-generated pages, sections and categories into the editor"
                                className="flex items-center gap-2 h-[40px] bg-indigo-500 text-white px-3 py-1 rounded-md hover:bg-indigo-600 text-sm font-medium"
                            >
                                <LayoutGrid size={16} />
                                {autoLayoutDone ? "Re-apply Layout" : "Auto Layout"}
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
                    <Tabs key={layoutKey} defaultValue={defaultTab}>
                        <TabList>
                            <Tab>Fragment</Tab>
                            <Tab>Categories</Tab>
                            <Tab>Pages</Tab>
                            <Tab>Section Components</Tab>
                            <Tab>Styling</Tab>
                            <Tab>Settings</Tab>
                            <Tab>
                                <span className="flex items-center gap-1">
                                    <Wand2 size={14} />
                                    AI Generate
                                </span>
                            </Tab>
                        </TabList>
                        <TabPanel value={0}>
                            <Fragment pages={data?.data?.pages ?? []} />
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
                            <Styling theme={liveTheme} onThemeChange={setLiveTheme} />
                        </TabPanel>
                        <TabPanel value={5}>
                            <Settings />
                        </TabPanel>
                        <TabPanel value={6}>
                            <div className="overflow-y-auto" style={{ maxHeight: "calc(100vh - 180px)" }}>
                                <InterfaceGenerate
                                    interfaceId={app_comp}
                                    systemId={systemId || ""}
                                    onVariantTokensChange={setLiveTheme}
                                />
                            </div>
                        </TabPanel>
                    </Tabs>
                </>
            )}
        </>
    );
};

export default ShowInterface;
