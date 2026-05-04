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
import { CircleUserRound, Save, Trash } from "lucide-react";
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { AgentDesign } from './AgentDesign';
import { Categories } from './Categories';
import { Pages } from './Pages';
import { Sections } from './Sections';
import { Styling } from './Styling';
import { Settings } from './Settings';


type Props = {
    systemId: string;
    app_comp: string;
};

const ShowInterface: React.FC<Props> = ({ app_comp }) => {
    const { data, isSuccess } = useInterface(app_comp);
    const navigate = useNavigate();
    const { systemId } = useParams();
    const [isSaving, setIsSaving] = useState(false);
    const [autoSaveEnabled, setAutoSaveEnabled] = useState(() => {
        if (typeof window === 'undefined') return false;
        return window.localStorage.getItem('interfaceAutoSave') === 'true';
    });
    const autoSaveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
    //const actorId = data?.actor || '';
    //const [actor, isSuccessActor] = useActor(systemId, actorId);

    const handleDelete = async () => {
        try {
            await deleteInterface(app_comp);
        } catch (error) {
            console.error('Error deleting interface:', error);
        }
        navigate(`/systems/${systemId}/interfaces`);
    };

    const handleSave = useCallback(async () => {
        if (!data) return;
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
    }, [app_comp, data, systemId]);

    const toggleAutoSave = () => {
        const next = !autoSaveEnabled;
        setAutoSaveEnabled(next);
        window.localStorage.setItem('interfaceAutoSave', String(next));
    };

    useEffect(() => {
        if (!autoSaveEnabled || !isSuccess) return;

        const watchedKeys = new Set(['styling', 'categories', 'pages', 'sections', 'settings']);
        const scheduleSave = () => {
            if (autoSaveTimer.current) clearTimeout(autoSaveTimer.current);
            autoSaveTimer.current = setTimeout(() => {
                handleSave();
            }, 700);
        };

        const onLocalStorageUpdate = (event: Event) => {
            const customEvent = event as CustomEvent<{ key?: string }>;
            const changedKey = customEvent.detail?.key;
            if (changedKey && watchedKeys.has(changedKey)) {
                scheduleSave();
            }
        };

        window.addEventListener('interface-local-storage-updated', onLocalStorageUpdate as EventListener);
        return () => {
            window.removeEventListener('interface-local-storage-updated', onLocalStorageUpdate as EventListener);
            if (autoSaveTimer.current) {
                clearTimeout(autoSaveTimer.current);
                autoSaveTimer.current = null;
            }
        };
    }, [autoSaveEnabled, handleSave, isSuccess]);

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
                                onClick={toggleAutoSave}
                                className={`h-[40px] px-3 rounded-md border text-sm font-medium transition-colors ${autoSaveEnabled ? 'bg-emerald-50 text-emerald-700 border-emerald-300 hover:bg-emerald-100' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'}`}
                            >
                                Auto Save: {autoSaveEnabled ? 'ON' : 'OFF'}
                            </button>
                            <button
                                onClick={handleSave}
                                className="w-[40px] h-[40px] bg-blue-500 text-white px-2 py-1 rounded-md hover:bg-blue-600 flex items-center justify-center"
                                disabled={isSaving}
                            >
                                {isSaving ? <CircularProgress /> : <Save />}
                            </button>
                            <button
                                className="w-[172px] h-[40px] bg-red-500 text-white px-2 py-1 rounded-md hover:bg-red-600"
                            >
                                <div>
                                    <button onClick={handleDelete} className="flex items-center gap-2">
                                        <Trash />
                                        Delete Interface
                                    </button>
                                </div>
                            </button>
                        </div>
                    </div>
                    <Tabs>
                        <TabList>
                            <Tab>Agent Design</Tab>
                            <Tab>Fragment</Tab>
                            <Tab>Categories</Tab>
                            <Tab>Pages</Tab>
                            <Tab>Section Components</Tab>
                            <Tab>Styling</Tab>
                            <Tab>Settings</Tab>
                        </TabList>
                        <TabPanel value={0}>
                            <AgentDesign interfaceId={app_comp} />
                        </TabPanel>
                        <TabPanel value={1}>
                            <p>Fragment</p>
                        </TabPanel>
                        <TabPanel value={2}>
                            <Categories />
                        </TabPanel>
                        <TabPanel value={3}>
                            <Pages actorName = {data?.name}/>
                        </TabPanel>
                        <TabPanel value={4}>
                            <Sections />
                        </TabPanel>
                        <TabPanel value={5}>
                            <Styling />
                        </TabPanel>
                        <TabPanel value={6}>
                            <Settings />
                        </TabPanel>
                    </Tabs>
                </>
            )}
        </>
    );
};

export default ShowInterface;
