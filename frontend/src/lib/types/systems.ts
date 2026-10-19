import type { DiagramOut } from "./diagrams";

export type SystemOut = {
    id: string;
    name: string;
    description: string;
    project: string;
    diagrams: DiagramOut[];
};

export type SystemCreate = {
    project_id: string;
    name: string;
    description?: string;
};

export type SystemUpdate = {
    name?: string;
    description?: string;
};