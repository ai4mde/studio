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
import { getInterface } from "../../../../api/metadata/interface";
import type { InterfaceRead } from "../../../../api/metadata/interface";
import { listAttributes } from "../../../../api/metadata/classMembers";
import { listClassifiers } from "../../../../api/metadata/classifier";
import { contentToEditor } from "../content";
import { saveInterfaceContent } from "../save";
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
    const [actorName, setActorName] = useState<string>("");

    // Write an interface into the editor's localStorage. The tabs read
    // localStorage when they mount, so they're only shown (loadedId) after this.
    const loadEditor = async (interfaceData: InterfaceRead) => {
        // The interface only stores ids, look up the names to show
        const classIds = Array.from(
            new Set(interfaceData.sections.map((s) => s.uml_class).filter(Boolean)),
        ) as string[];
        const attributeLists = await Promise.all(classIds.map((id) => listAttributes(id)));
        const attributesById = Object.fromEntries(
            attributeLists.flat().map((a) => [a.id, a]),
        );

        const classifiers = await listClassifiers({ system_id: interfaceData.system });
        const nameOf = (id: string | null | undefined) =>
            ((classifiers.find((c) => c.id === id)?.data ?? {}) as { name?: string }).name ?? "";
        const actionNames = Object.fromEntries(
            classifiers
                .filter((c) => c.type === "action")
                .map((c) => [c.id, nameOf(c.id)]),
        );

        const { categories, sections, pages } = contentToEditor(
            interfaceData,
            attributesById,
            actionNames,
        );

        localStorage.setItem('styling', JSON.stringify({
            radius: interfaceData.radius,
            backgroundColor: interfaceData.background_color,
            textColor: interfaceData.text_color,
            accentColor: interfaceData.accent_color,
            selectedStyle: interfaceData.style,
        }));
        localStorage.setItem('settings', JSON.stringify({
            managerAccess: interfaceData.manager_access,
        }));
        localStorage.setItem('categories', JSON.stringify(categories));
        localStorage.setItem('sections', JSON.stringify(sections));
        localStorage.setItem('pages', JSON.stringify(pages));

        setActorName(nameOf(interfaceData.actor));
        setLoadedId(interfaceData.id ?? null);
    };

    useEffect(() => {
        if (!data) return;
        loadEditor(data);
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
            // Save with the interface as the backend has it now, then reload the
            // editor so it uses the new ids the backend gave the saved items
            const current = await getInterface(app_comp);
            await saveInterfaceContent(current, categories, pages, sections);

            const saved = await getInterface(app_comp);
            setLoadedId(null);
            await loadEditor(saved);
        } catch (error) {
            console.error('Error saving interface:', error);
            alert("Saving the interface failed, see the console for details.");
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
                                <h4 className="text-l">{actorName || 'Unknown'}</h4>
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
