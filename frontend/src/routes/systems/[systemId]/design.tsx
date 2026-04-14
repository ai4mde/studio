import { authAxios } from "$lib/features/auth/state/auth";
import SystemLayout from "$lib/features/browser/components/systems/SystemLayout";
import { useSystem } from "$browser/queries";
import { RefreshCw, AlertTriangle } from "lucide-react";
import React, { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router";

const SystemDesign: React.FC = () => {
    const { systemId } = useParams();
    const { data: system } = useSystem(systemId);
    const navigate = useNavigate();
    const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
    const [errorMsg, setErrorMsg] = useState("");
    const started = useRef(false);

    useEffect(() => {
        if (!systemId || !system || started.current) return;
        started.current = true;
        setStatus("loading");

        (async () => {
            try {
                // 1. Fetch system export metadata
                const exportRes = await authAxios.get("/v1/metadata/systems/export/", {
                    params: { system_ids: systemId },
                });
                const exportData = exportRes.data;
                if (!exportData || exportData.length === 0) {
                    throw new Error("No metadata found for this system.");
                }
                const metadata = JSON.stringify(exportData[0]);

                // 2. Run the pipeline (long-running, increase timeout)
                const runRes = await authAxios.post("/v1/generator/pipeline/run/", {
                    project_name: system.name || "Project",
                    application_name: system.name || "Application",
                    metadata,
                    system_id: systemId,
                    authentication_present: true,
                }, { timeout: 300000 });

                const threadId = runRes.data.thread_id;
                if (!threadId) {
                    throw new Error("Pipeline did not return a thread_id.");
                }

                // 3. Navigate to design refine page
                navigate(`/design/${threadId}`, { replace: true });
            } catch (err: unknown) {
                setStatus("error");
                setErrorMsg(err instanceof Error ? err.message : "Pipeline failed.");
            }
        })();
    }, [systemId, system, navigate]);

    return (
        <SystemLayout>
            <div className="flex h-full w-full items-center justify-center">
                {status === "loading" && (
                    <div className="flex flex-col items-center gap-3 text-gray-500">
                        <RefreshCw size={28} className="animate-spin text-indigo-500" />
                        <span className="text-sm font-medium">Running design pipeline...</span>
                        <span className="text-xs text-gray-400">
                            This may take a moment. You will be redirected automatically.
                        </span>
                    </div>
                )}
                {status === "error" && (
                    <div className="flex flex-col items-center gap-3 text-gray-500">
                        <AlertTriangle size={28} className="text-red-500" />
                        <span className="text-sm font-medium text-red-600">Pipeline failed</span>
                        <span className="text-xs text-gray-500">{errorMsg}</span>
                        <button
                            onClick={() => {
                                started.current = false;
                                setStatus("idle");
                            }}
                            className="mt-2 rounded-md border border-gray-200 px-4 py-1.5 text-xs text-indigo-600 hover:bg-gray-50"
                        >
                            Retry
                        </button>
                    </div>
                )}
                {status === "idle" && (
                    <span className="text-sm text-gray-400">Preparing...</span>
                )}
            </div>
        </SystemLayout>
    );
};

export default SystemDesign;
