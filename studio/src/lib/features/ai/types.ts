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
