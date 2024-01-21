import Layout from "$lib/shared/components/Layout/Layout";
import React from "react";
import { Outlet } from "react-router";

export const IndexPage: React.FC = () => {
    return <>
        <Layout>
            <Outlet/>
        </Layout>
    </>
}

export default IndexPage