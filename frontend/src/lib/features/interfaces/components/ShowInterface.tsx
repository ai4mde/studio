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
import { InterfaceDesigner } from './InterfaceDesigner';
import { Categories } from './Categories';
import { Pages } from './Pages';
import { Sections } from './Sections';
import { Styling } from './Styling';
import { Settings } from './Settings';
import { PageRegions } from './PageRegions';
import useLocalStorage from './useLocalStorage';


type Props = {
    systemId: string;
    app_comp: string;
};

const ShowInterface: React.FC<Props> = ({ app_comp }) => {
    const { data, isSuccess, isLoading, isError, error } = useInterface(app_comp);
    const navigate = useNavigate();
    const { systemId } = useParams();
    const [, setStyling] = useLocalStorage('styling', {});
    const [, setCategories] = useLocalStorage('categories', []);
    const [, setPages] = useLocalStorage('pages', []);
    const [, setSections] = useLocalStorage('sections', []);
    const [, setSettings] = useLocalStorage('settings', {});
    const [, setScopedStyling] = useLocalStorage(`interface:${app_comp}:styling`, {});
    const [, setScopedCategories] = useLocalStorage(`interface:${app_comp}:categories`, []);
    const [, setScopedPages] = useLocalStorage(`interface:${app_comp}:pages`, []);
    const [, setScopedSections] = useLocalStorage(`interface:${app_comp}:sections`, []);
    const [, setScopedSettings] = useLocalStorage(`interface:${app_comp}:settings`, {});
    const [isSaving, setIsSaving] = useState(false);
    const [activeTab, setActiveTab] = useState<number | string>(0);
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
        const scoped = (key: string, fallback: string) => {
            const raw = localStorage.getItem(`interface:${app_comp}:${key}`) ?? localStorage.getItem(fallback);
            return raw ? JSON.parse(raw) : (key === 'styling' || key === 'settings' ? {} : []);
        };
        const styling = scoped('styling', 'styling');
        const categories = scoped('categories', 'categories');
        const pages = scoped('pages', 'pages');
        const sections = scoped('sections', 'sections');
        const settings = scoped('settings', 'settings');

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
        if (!isSuccess || !data?.data) return;

        let interfaceData = data.data as any;
        if (typeof interfaceData === 'string') {
            try {
                interfaceData = JSON.parse(interfaceData);
            } catch (error) {
                console.error('Error parsing interface data:', error);
                return;
            }
        }

        setStyling(interfaceData.styling || {});
        setCategories(interfaceData.categories || []);
        setPages(interfaceData.pages || []);
        setSections(interfaceData.sections || []);
        setSettings(interfaceData.settings || {});
        setScopedStyling(interfaceData.styling || {});
        setScopedCategories(interfaceData.categories || []);
        setScopedPages(interfaceData.pages || []);
        setScopedSections(interfaceData.sections || []);
        setScopedSettings(interfaceData.settings || {});
    }, [data?.data, isSuccess]);

    useEffect(() => {
        if (!autoSaveEnabled || !isSuccess) return;

        const watchedKeys = new Set([
            'styling',
            'categories',
            'pages',
            'sections',
            'settings',
            `interface:${app_comp}:styling`,
            `interface:${app_comp}:categories`,
            `interface:${app_comp}:pages`,
            `interface:${app_comp}:sections`,
            `interface:${app_comp}:settings`,
        ]);
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

    if (isLoading) {
        return (
            <div className="flex h-[240px] items-center justify-center text-sm text-gray-500">
                Loading interface...
            </div>
        );
    }

    if (isError) {
        return (
            <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                Could not load this interface: {(error as any)?.message || 'Unknown error'}
            </div>
        );
    }

    if (!isSuccess || !data) {
        return (
            <div className="rounded-md border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">
                No interface data is available.
            </div>
        );
    }

    return (
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
                    <Tabs value={activeTab} onChange={(_, value) => setActiveTab(value ?? 0)}>
                        <TabList id="tour-tablist">
                            <Tab id="tour-tab-agent-design">Interface Designer</Tab>
                            <Tab>Fragment</Tab>
                            <Tab>Categories</Tab>
                            <Tab id="tour-tab-pages">Pages</Tab>
                            <Tab>Page Layout</Tab>
                            <Tab id="tour-tab-sections">Section Components</Tab>
                            <Tab>Styling</Tab>
                            <Tab>Settings</Tab>
                        </TabList>
                        <TabPanel value={0}>
                            {activeTab === 0 && <InterfaceDesigner interfaceId={app_comp} systemId={systemId} />}
                        </TabPanel>
                        <TabPanel value={1}>
                            <p>Fragment</p>
                        </TabPanel>
                        <TabPanel value={2}>
                            {activeTab === 2 && <Categories />}
                        </TabPanel>
                        <TabPanel value={3}>
                            {activeTab === 3 && <Pages actorName={data?.name} interfaceId={app_comp} />}
                        </TabPanel>
                        <TabPanel value={4}>
                            {activeTab === 4 && <PageRegions />}
                        </TabPanel>
                        <TabPanel value={5}>
                            {activeTab === 5 && <Sections interfaceId={app_comp} />}
                        </TabPanel>
                        <TabPanel value={6}>
                            {activeTab === 6 && <Styling />}
                        </TabPanel>
                        <TabPanel value={7}>
                            {activeTab === 7 && <Settings />}
                        </TabPanel>
                    </Tabs>
        </>
    );
};

export default ShowInterface;
