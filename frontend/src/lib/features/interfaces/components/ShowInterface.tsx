import {
    Tabs,
    Tab,
    TabList,
    TabPanel,
} from '@mui/joy'
import { Save, Trash } from "lucide-react";
import React from 'react'
import { useInterface } from "$browser/queries";
import { useDeleteInterface } from '$browser/mutations';
import { Styling } from './Styling';
import { Categories } from './Categories';
import { Pages } from './Pages';
import { Sections } from './Sections';

type Props = {
    projectId: string
    systemId: string
    interfaceId: string
} 

const ShowInterface: React.FC<Props> = ({ app_comp }) => {

    const { data, isSuccess } = useInterface(app_comp);
    const { mutate, isLoading, isError, error } = useDeleteInterface();

    const handleDelete = async () => {
        try {
          await mutate(app_comp);
          console.log('Interface deleted');
        } catch (error) {
          console.error('Error deleting interface:', error);
        }
      };

    return (
        <>
            {isSuccess && (
                <>       
                    <div className="flex items-center justify-between w-full gap-4">
                        <h3 className="text-xl font-bold">{data.name}</h3>
                        <div className="flex gap-4 ml-auto">
                            <button
                                className="w-[40px] h-[40px] bg-blue-500 text-white px-2 py-1 rounded-md hover:bg-blue-600"
                            >
                                <Save />
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
                                    <button onClick={handleDelete} disabled={isLoading} className="flex items-center gap-2">
                                        <Trash />
                                        Delete Interface
                                    </button>
                                    {isLoading && <p>Deleting...</p>}
                                    {isError && <p>Error: {error?.message}</p>}
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