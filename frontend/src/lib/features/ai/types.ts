export type Pipeline = {
    id: string;
    requirements: string;
    output?: any;
    created_at: string;
    updated_at: string;
    type: "metadata" | "bucketing";
    step: number;
    url: string;
};

export type HitlCandidate = {
    candidate_id: string;
    candidate_index: number;
    candidate_count: number;
    session_id: string;
    project_id: string;
    system_id: string;
    name: string;
    process_text: string;
    pipeline_profile: string;
    provisional: boolean;
    ai4mde: any;
    activity_graph?: {
        nodes: Array<Record<string, any>>;
        edges: Array<Record<string, any>>;
    };
};

export type HitlNodePositions = Record<
    string,
    {
        x: number;
        y: number;
    }
>;

export type HitlCandidateGenerationResponse = {
    session_id: string;
    project_id: string;
    mode: "refinement" | "baseline";
    pipeline_profile: string;
    candidates: HitlCandidate[];
    systems: HitlCandidate[];
};

export type HitlSelectedCandidateResponse = {
    candidate_id: string;
    candidate_index: number;
    candidate_count: number;
    session_id: string;
    project_id: string;
    system_id: string;
    diagram_id?: string | null;
    name: string;
    process_text: string;
    pipeline_profile: string;
    provisional: false;
    current_revision_id: string;
    revision_id: string;
    revision_index: number;
    revision_origin: "baseline" | "human_sync" | "ai_refinement";
    parent_revision_id?: string | null;
    ui_path?: string;
};

export type HitlRevision = {
    revision_id: string;
    revision_index: number;
    parent_revision_id?: string | null;
    pipeline_profile: string;
    revision_origin: "baseline" | "human_sync" | "ai_refinement";
    candidate_index?: number | null;
    candidate_count?: number | null;
    refinement_instruction?: string | null;
    created_at: string;
    is_current: boolean;
};

export type HitlRevisionHistoryResponse = {
    system_id: string;
    process_text?: string | null;
    current_revision_id?: string | null;
    revisions: HitlRevision[];
};
