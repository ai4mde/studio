import { authAxios } from "$auth/state/auth";
import { useMutation, useQuery } from "@tanstack/react-query";

export type ScreenInfo = {
    page_id: string;
    page_name: string;
    screen_type: string;
    has_create: boolean;
    has_update: boolean;
    has_delete: boolean;
    models: string[];
    sections_count: number;
};

export type UXDraft = {
    objects: string[];
    screens: string[];
    actor_screens: Record<string, string[]>;
    actor_types: Record<string, "staff" | "external">;
    flows: string[];
    ui_suggestions: string[];
};

export type UXReview = {
    issues: string[];
    improvements: string[];
    final_version: UXDraft;
};

export type UIDesign = {
    base_html: string;
    style_css: string;
    style_guide: {
        primary: string;
        secondary: string;
        accent: string;
        background: string;
        text_primary: string;
        text_secondary: string;
        font_heading: string;
        font_body: string;
        border_radius: string;
        shadow: string;
        pattern: string;
        ui_kit: string;
        mood: string;
    };
    page_previews: Record<string, string> | null;
    actor_base_html: Record<string, string> | null;
    page_designs: Record<string, Record<string, unknown>> | null;
};

export type PipelineStatus = {
    thread_id: string;
    interrupted: boolean;
    screens: ScreenInfo[];
    ux_draft: UXDraft | null;
    ux_review: UXReview | null;
    ui_design: UIDesign | null;
    use_llm_views: boolean;
    success: boolean;
    error: string | null;
};

export type RunPipelineInput = {
    project_name: string;
    application_name: string;
    metadata: string;
    system_id: string;
    authentication_present: boolean;
};

export type ResumeInput = {
    approved: boolean;
    feedback?: string;
};

export const useRunPipeline = () =>
    useMutation<PipelineStatus, Error, RunPipelineInput>({
        mutationFn: async (body) => {
            const { data } = await authAxios.post("/v1/generator/pipeline/run/", body);
            return data;
        },
    });

export const usePipelineStatus = (threadId: string | null) =>
    useQuery<PipelineStatus>({
        queryKey: ["pipeline", threadId],
        queryFn: async () => {
            const { data } = await authAxios.get(`/v1/generator/pipeline/${threadId}/`);
            return data;
        },
        enabled: !!threadId,
        refetchInterval: (query) => {
            // Stop polling once finished (not interrupted and has result)
            const d = query.state.data;
            if (d && !d.interrupted && (d.success || d.error)) return false;
            return 3000;
        },
    });

export const useResumePipeline = (threadId: string) =>
    useMutation<PipelineStatus, Error, ResumeInput>({
        mutationFn: async (body) => {
            const { data } = await authAxios.post(
                `/v1/generator/pipeline/${threadId}/resume/`,
                body,
            );
            return data;
        },
    });

// ── Generator pipeline (new AST-based pipeline) ───────────────────────────────

export type GeneratorPage = {
    page_id: string;
    name: string;
    ast?: unknown[];
    regions?: unknown[];
};

export type GeneratorApp = {
    actor_id: string;
    actor_name: string;
    pages: GeneratorPage[];
};

export type GeneratorTheme = {
    name: string;
    tokens: Record<string, string>;
};

export type LayoutElement = {
    html: string;
    position: 'top' | 'left' | 'right' | 'bottom';
    config?: Record<string, unknown>;
};

export type LayoutOption = {
    id: string;
    name: string;
    description: string;
    elements: Record<string, LayoutElement>;
};

export type GeneratorPipelineStatus = {
    thread_id: string;
    system_id: string | null;
    ui_design: { ui_ir: { apps: GeneratorApp[] } } | null;
    page_ir: unknown | null;
    flow_graph: unknown | null;
    theme: GeneratorTheme | null;
    layout_options: LayoutOption[] | null;
    global_layout: Record<string, LayoutElement> | null;
};

export const useGeneratorPipeline = (threadId?: string) =>
    useQuery<GeneratorPipelineStatus>({
        queryKey: ["generator-pipeline", threadId],
        queryFn: async () => {
            const { data } = await authAxios.get(`/v1/generator/pipeline/${threadId}/`);
            return data;
        },
        enabled: !!threadId,
    });

export const useRefinePipeline = (threadId: string) =>
    useMutation<GeneratorPipelineStatus, Error, { prompt: string }>({
        mutationFn: async (body) => {
            const { data } = await authAxios.post(
                `/v1/generator/pipeline/${threadId}/refine/`,
                body,
            );
            return data;
        },
    });

export const useSelectLayout = (threadId: string) =>
    useMutation<GeneratorPipelineStatus, Error, { option_id: string }>({
        mutationFn: async (body) => {
            const { data } = await authAxios.post(
                `/v1/generator/pipeline/${threadId}/layout/select/`,
                body,
            );
            return data;
        },
    });
