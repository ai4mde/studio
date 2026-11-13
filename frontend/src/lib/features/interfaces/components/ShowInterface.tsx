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
import { replaceInterfaceContent } from "../../../../api/metadata/interface";
import { listAttributes } from "../../../../api/metadata/classMembers";
import { listClassifiers } from "../../../../api/metadata/classifier";
import { contentToEditor, editorToContent } from "../content";
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

    // Load the interface into the editor. The tabs read localStorage when they
    // mount, so only show them (loadedId) once everything is written.
    useEffect(() => {
        if (!data) return;
        let cancelled = false;

        const load = async () => {
            // The interface only stores ids, look up the names to show
            const classIds = Array.from(
                new Set(data.sections.map((s) => s.uml_class).filter(Boolean)),
            ) as string[];
            const attributeLists = await Promise.all(classIds.map((id) => listAttributes(id)));
            const attributesById = Object.fromEntries(
                attributeLists.flat().map((a) => [a.id, a]),
            );

            const classifiers = await listClassifiers({ system_id: data.system });
            const actionNames = Object.fromEntries(
                classifiers
                    .filter((c) => c.type === "action")
                    .map((c) => [c.id, (c.data as { name?: string }).name ?? ""]),
            );

            const { categories, sections, pages } = contentToEditor(
                data,
                attributesById,
                actionNames,
            );

            if (cancelled) return;

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
            localStorage.setItem('categories', JSON.stringify(categories));
            localStorage.setItem('sections', JSON.stringify(sections));
            localStorage.setItem('pages', JSON.stringify(pages));

            setLoadedId(data.id ?? null);
        };

        load();
        return () => {
            cancelled = true;
        };
    }, [data?.id]);

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
            await replaceInterfaceContent(
                app_comp,
                editorToContent(categories, pages, sections),
            );
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
                            <Pages actorId={data?.actor} />
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
