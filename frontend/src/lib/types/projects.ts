export type ProjectOut = {
    id: string;
    name: string;
    description: string;
};

export type ProjectCreate = {
    name: string;
    description?: string;
};

export type ProjectUpdate = {
    name?: string;
    description?: string;
};