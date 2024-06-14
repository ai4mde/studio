import {
    Tabs,
    Tab,
    TabList,
    TabPanel,
} from '@mui/joy'
import React, { useEffect, useState } from 'react'
import { useInterface } from "$browser/queries";

type Props = {
    projectId: string
    systemId: string
    interfaceId: string
} 

const ShowInterface: React.FC<Props> = ({ app_comp }) => {

    const { data, isSuccess } = useInterface(app_comp);
    return (
        <>
            {isSuccess && (
                <>
                    <h3 className="text-xl font-bold">{data.name}</h3>
                    
                    <Tabs>
                        <TabList>
                            <Tab>Fragment</Tab>
                            <Tab>Categories</Tab>
                            <Tab>Section Components</Tab>
                            <Tab>Styling</Tab>
                        </TabList>
                        <TabPanel value={0}>
                            <p>Fragment</p>
                        </TabPanel>
                        <TabPanel value={1}>
                            <p>Categories</p>
                        </TabPanel>
                        <TabPanel value={2}>
                            <p>Pages</p>
                        </TabPanel>
                        <TabPanel value={3}>
                            <p>Section Components</p>
                        </TabPanel>
                        <TabPanel value={4}>
                            <p>Styling</p>
                        </TabPanel>
                    </Tabs>
                </>
            )}
        </>
    )
}

export default ShowInterface