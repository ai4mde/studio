import {
    Tabs,
    Tab,
    TabList,
    TabPanel,
    CircularProgress,
} from '@mui/joy'
import { Save, Trash } from "lucide-react";
import React, { useState } from 'react'
import { useInterface } from "$browser/queries";
import { deleteInterface } from '$browser/mutations';
import { Styling } from './Styling';
import { Categories } from './Categories';
import { Pages } from './Pages';
import { Sections } from './Sections';
import { useNavigate, useParams } from 'react-router-dom';
import { authAxios } from '$auth/state/auth';


type Props = {
    projectId: string
    systemId: string
    app_comp: string
    interfaceId: string
} 

const ShowInterface: React.FC<Props> = ({ app_comp }) => {

    const { data, isSuccess } = useInterface(app_comp);
    const navigate = useNavigate();
    const { systemId } = useParams();
    const [isSaving, setIsSaving] = useState(false);

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

        console.log(styling);
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
                },
            });
        } catch (error) {
            console.error('Error saving interface:', error);
        } finally {
            setTimeout(function(){
                setIsSaving(false);
            }, 200);
        }
    }

    return (
        <>
            {isSuccess && (
                <>       
                    <div className="flex items-center justify-between w-full gap-4">
                        <h3 className="text-xl font-bold">{data.name}</h3>
                        <div className="flex gap-4 ml-auto">
                            <button
                                onClick={handleSave}
                                className="w-[40px] h-[40px] bg-blue-500 text-white px-2 py-1 rounded-md hover:bg-blue-600 flex items-center justify-center"
                                disabled={isSaving}
                            >
                                {isSaving ? <CircularProgress /> : <Save />}
                            </button>
                            <button
                                className="w-[140px] h-[40px] bg-gray-400 text-white px-2 py-1 rounded-md hover:bg-gray-500"
                            >
                                Discard changes
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
                        </TabList>
                        <TabPanel value={0}>
                            <p>Fragment</p>
                        </TabPanel>
                        <TabPanel value={1}>
                            <Categories app_comp={app_comp} />
                        </TabPanel>
                        <TabPanel value={2}>
                            <Pages app_comp={app_comp} />
                        </TabPanel>
                        <TabPanel value={3}>
                            <Sections app_comp={app_comp} />
                        </TabPanel>
                        <TabPanel value={4}>
                            <Styling app_comp={app_comp} />
                        </TabPanel>
                    </Tabs>
                </>
            )}
        </>
    )
}

export default ShowInterface