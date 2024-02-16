import Layout from "$lib/shared/components/Layout/Layout";
import { queryClient } from "$shared/hooks/queryClient";
import "@fontsource/ibm-plex-mono";
import "@fontsource/inter";
import { CircularProgress } from "@mui/joy";
import { QueryClientProvider } from "@tanstack/react-query";
import React, { Suspense } from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter as Router, useRoutes } from "react-router-dom";
import * as Sentry from "@sentry/browser";

import routes from "~react-pages";
import "./index.css";
import { useAuthEffect } from "$auth/hooks/authEffect";

Sentry.init({
    dsn: import.meta.env.AI4MDE_SENTRY_DSN,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration({
        maskAllText: false,
        blockAllMedia: false,
      }),
    ],
    tracesSampleRate: 1.0,
    tracePropagationTargets: ["localhost", /^https:\/\/ai4mde-api\.semax\.nguml\.com\//],
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
    enabled: !!import.meta.env.AI4MDE_SENTRY_DSN,
});

export const App: React.FC = () => {
    // useAuthEffect is a custom hook that runs housekeeping tasks on the auth state
    useAuthEffect(); // TODO: Find a better place to put this

    return (
        <>
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
        </>
    );
};

ReactDOM.createRoot(document.getElementById("root")!).render(
    <React.StrictMode>
        <QueryClientProvider client={queryClient}>
            <Router>
                <App />
            </Router>
        </QueryClientProvider>
    </React.StrictMode>,
);
