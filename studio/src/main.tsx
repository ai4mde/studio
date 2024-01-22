import Layout from "$lib/shared/components/Layout/Layout";
import { queryClient } from "$shared/hooks/queryClient";
import "@fontsource/ibm-plex-mono";
import "@fontsource/inter";
import { CircularProgress } from "@mui/joy";
import React, { Suspense } from "react";
import ReactDOM from "react-dom/client";
import { QueryClientProvider } from "react-query";
import { BrowserRouter as Router, useRoutes } from "react-router-dom";
import routes from "~react-pages";
import "./index.css";

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
        <QueryClientProvider client={queryClient}>
            <Router>
                <App />
            </Router>
        </QueryClientProvider>
    </React.StrictMode>
);
