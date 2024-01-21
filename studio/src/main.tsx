import React, { Suspense } from "react";
import ReactDOM from "react-dom/client";
import "@fontsource/ibm-plex-mono";
import "@fontsource/inter";
import "./index.css";
import { BrowserRouter as Router, useRoutes } from "react-router-dom";
import routes from "~react-pages";
import Layout from "$lib/shared/components/Layout/Layout";
import { CircularProgress } from "@mui/joy";

export const App: React.FC = () => {
    return (
        <Layout>
            <Suspense
                fallback={
                    <>
                        <CircularProgress className="animate-spin" />
                    </>
                }
            >
                {useRoutes(routes)}
            </Suspense>
        </Layout>
    );
};

ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
        <Router>
            <App />
        </Router>
    </React.StrictMode>
);
