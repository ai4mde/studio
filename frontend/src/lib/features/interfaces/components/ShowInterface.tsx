import { authAxios } from '$auth/state/auth';
import {
    useDeleteInterface,
    useInterface,
    useUpdateInterface,
} from "../../../../api/metadata/hooks/interface";
import {
    CircularProgress,
    Tab,
    TabList,
    TabPanel,
    Tabs,
} from '@mui/joy';
import { CircleUserRound, Save, Trash } from "lucide-react";
import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
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
    const deleteInterface = useDeleteInterface();
    const updateInterface = useUpdateInterface();
    const navigate = useNavigate();
    const { systemId } = useParams();
    const [isSaving, setIsSaving] = useState(false);
    const [loadedId, setLoadedId] = useState<string | null>(null);

    // Styling and settings are now plain fields on the interface, so load them
    // into the local editor state when the interface is opened
    useEffect(() => {
        if (!data) return;

        localStorage.setItem('styling', JSON.stringify({
            radius: data.radius,
            backgroundColor: data.background_color,
            textColor: data.text_color,
            accentColor: data.accent_color,
            selectedStyle: data.style,
        }));
        localStorage.setItem('settings', JSON.stringify({
            managerAccess: data.manager_access,
        }));
        // Only render the tabs after this, they read localStorage when they mount
        setLoadedId(data.id ?? null);
    }, [data?.id]);
    //const actorId = data?.actor || '';
    //const [actor, isSuccessActor] = useActor(systemId, actorId);

    const handleDelete = async () => {
        try {
            await deleteInterface.mutateAsync(app_comp);
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
            await updateInterface.mutateAsync({
                interfaceId: app_comp,
                payload: {
                    radius: styling.radius ?? null,
                    background_color: styling.backgroundColor ?? null,
                    text_color: styling.textColor ?? null,
                    accent_color: styling.accentColor ?? null,
                    style: styling.selectedStyle ?? null,
                    manager_access: settings.managerAccess ?? null,
                },
            });
        } catch (error) {
            console.error('Error saving interface:', error);
        }

        try {
            // TODO(api): categories, pages and sections now have their own endpoints,
            // to be discussed how the editor should save them. This old call still fails.
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
            {isSuccess && loadedId === data.id && (
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
                            <Styling />
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
